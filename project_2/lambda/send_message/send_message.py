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

MAX_TEXT_LENGTH = 1000


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


def parse_body(body: str | None) -> dict[str, object] | None:
    if not body:
        return None

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    return cast(dict[str, object], parsed)


def validate_text(text: object) -> bool:
    return isinstance(text, str) and 0 < len(text) <= MAX_TEXT_LENGTH


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


def broadcast_message(
    event: Event, table: DynamoDbTable, payload: Mapping[str, str]
) -> int:
    client = get_management_client(event)
    encoded_payload = json.dumps(payload).encode("utf-8")
    recipients = 0

    for connection in scan_connections(table):
        connection_id = connection["connectionId"]
        try:
            client.post_to_connection(ConnectionId=connection_id, Data=encoded_payload)
            recipients += 1
        except client.exceptions.GoneException:
            logger.info(
                "Cleaning stale connection during message broadcast: %s", connection_id
            )
            table.delete_item(Key={"connectionId": connection_id})
        except Exception:
            logger.exception(
                "Message broadcast failed for connection %s", connection_id
            )

    return recipients


def handler(event: Event, context: object) -> dict[str, str | int]:
    del context

    try:
        request_context = get_request_context(event)
        connection_id = request_context.get("connectionId")
        if not isinstance(connection_id, str) or not connection_id:
            logger.error("Missing connectionId in requestContext")
            return {"statusCode": 400, "body": "Invalid request"}

        raw_body = event.get("body")
        body = parse_body(raw_body if isinstance(raw_body, str) else None)
        if body is None or body.get("action") != "sendMessage":
            logger.warning("Invalid message payload: %s", event.get("body"))
            return {"statusCode": 400, "body": "Invalid JSON"}

        text = body.get("text")
        if not validate_text(text):
            logger.warning("Invalid text from %s", connection_id)
            return {"statusCode": 400, "body": "Missing or invalid text"}
        assert isinstance(text, str)

        table = get_table()
        sender = table.get_item(Key={"connectionId": connection_id}).get("Item")
        callsign = sender.get("callsign") if isinstance(sender, dict) else None
        if not isinstance(callsign, str):
            logger.warning("Unknown sender: %s", connection_id)
            return {"statusCode": 400, "body": "Unknown sender"}

        payload: dict[str, str] = {
            "type": "message",
            "callsign": callsign,
            "text": text,
            "timestamp": utc_timestamp(),
        }
        recipient_count = broadcast_message(event, table, payload)

        logger.info(
            "Broadcast message from %s to %s active connections",
            callsign,
            recipient_count,
        )
        return {"statusCode": 200, "body": "Message sent"}
    except Exception:
        logger.exception("send_message handler failed")
        return {"statusCode": 500, "body": "Internal server error"}
