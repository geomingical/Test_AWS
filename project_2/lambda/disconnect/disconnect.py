import json
import logging
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from importlib import import_module
from typing import Protocol, cast

boto3 = import_module("boto3")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DynamoDbTable(Protocol):
    def scan(self, **kwargs: object) -> dict[str, object]: ...

    def get_item(self, *, Key: dict[str, str]) -> dict[str, object]: ...

    def delete_item(self, *, Key: dict[str, str]) -> dict[str, object]: ...


class DynamoDbResource(Protocol):
    def Table(self, name: str) -> DynamoDbTable: ...


class ManagementExceptions(Protocol):
    GoneException: type[Exception]


class ApiGatewayManagementClient(Protocol):
    exceptions: ManagementExceptions

    def post_to_connection(self, *, ConnectionId: str, Data: bytes) -> object: ...


Event = Mapping[str, object]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_request_context(event: Event) -> Mapping[str, object]:
    request_context = event.get("requestContext")
    return request_context if isinstance(request_context, Mapping) else {}


def get_table() -> DynamoDbTable:
    dynamodb_kwargs: dict[str, str] = {}
    dynamodb_endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if dynamodb_endpoint:
        dynamodb_kwargs["endpoint_url"] = dynamodb_endpoint

    dynamodb = cast(DynamoDbResource, boto3.resource("dynamodb", **dynamodb_kwargs))
    return dynamodb.Table(os.environ.get("TABLE_NAME", "ChatConnections"))


def get_management_client(event: Event) -> ApiGatewayManagementClient:
    request_context = get_request_context(event)
    domain_name = request_context.get("domainName")
    stage = request_context.get("stage")
    if not isinstance(domain_name, str) or not isinstance(stage, str):
        raise ValueError("Missing domainName or stage in requestContext")

    return cast(
        ApiGatewayManagementClient,
        boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=f"https://{domain_name}/{stage}",
        ),
    )


def scan_connections(table: DynamoDbTable) -> list[dict[str, str]]:
    connections: list[dict[str, str]] = []
    scan_kwargs: dict[str, object] = {"ProjectionExpression": "connectionId"}

    while True:
        response = table.scan(**scan_kwargs)
        items = response.get("Items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    connection_id = item.get("connectionId")
                    if isinstance(connection_id, str):
                        connections.append({"connectionId": connection_id})

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            return connections
        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key


def broadcast_user_left(event: Event, table: DynamoDbTable, callsign: str) -> None:
    try:
        client = get_management_client(event)
        payload = json.dumps(
            {
                "type": "system",
                "event": "user_left",
                "callsign": callsign,
                "timestamp": utc_timestamp(),
            }
        ).encode("utf-8")

        for connection in scan_connections(table):
            connection_id = connection["connectionId"]
            try:
                client.post_to_connection(ConnectionId=connection_id, Data=payload)
            except client.exceptions.GoneException:
                logger.info(
                    "Cleaning stale connection during leave broadcast: %s",
                    connection_id,
                )
                table.delete_item(Key={"connectionId": connection_id})
            except Exception:
                logger.exception(
                    "Leave broadcast failed for connection %s", connection_id
                )
    except Exception:
        logger.exception("Leave broadcast failed")


def handler(event: Event, context: object) -> dict[str, str | int]:
    del context

    try:
        request_context = get_request_context(event)
        connection_id = request_context.get("connectionId")
        if not isinstance(connection_id, str) or not connection_id:
            logger.error("Missing connectionId in requestContext")
            return {"statusCode": 400, "body": "Invalid request"}

        table = get_table()
        response = table.get_item(Key={"connectionId": connection_id})
        item = response.get("Item")
        if isinstance(item, dict) and isinstance(item.get("callsign"), str):
            callsign = cast(str, item.get("callsign"))
        else:
            callsign = "unknown"

        _ = table.delete_item(Key={"connectionId": connection_id})
        broadcast_user_left(event, table, callsign)

        logger.info("Deleted connection %s for callsign %s", connection_id, callsign)
        return {"statusCode": 200, "body": "Disconnected"}
    except Exception:
        logger.exception("Disconnect handler failed")
        return {"statusCode": 500, "body": "Internal server error"}
