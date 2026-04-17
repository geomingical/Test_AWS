import { useCallback, useEffect, useRef, useState } from "react";
import type { ConnectionStatus, SendMessagePayload, ServerMessage } from "../types";
import {
  RECONNECT_BASE_DELAY_MS,
  RECONNECT_MAX_ATTEMPTS,
  RECONNECT_MAX_DELAY_MS,
  WS_ENDPOINT,
} from "../config";

interface UseWebSocketReturn {
  status: ConnectionStatus;
  messages: ServerMessage[];
  sendMessage: (text: string) => void;
  connect: (callsign: string) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [messages, setMessages] = useState<ServerMessage[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const callsignRef = useRef("");
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intentionalCloseRef = useRef(false);
  const openConnectionRef = useRef<(callsign: string) => void>(() => {});

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (retriesRef.current >= RECONNECT_MAX_ATTEMPTS) {
      setStatus("disconnected");
      return;
    }

    setStatus("reconnecting");
    const delay = Math.min(
      RECONNECT_BASE_DELAY_MS * Math.pow(2, retriesRef.current),
      RECONNECT_MAX_DELAY_MS,
    );
    retriesRef.current += 1;

    reconnectTimerRef.current = setTimeout(() => {
      openConnectionRef.current(callsignRef.current);
    }, delay);
  }, []);

  const openConnection = useCallback(
    (callsign: string) => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      callsignRef.current = callsign;
      intentionalCloseRef.current = false;
      setStatus("connecting");

      const url = `${WS_ENDPOINT}?callsign=${encodeURIComponent(callsign)}`;
      const ws = new WebSocket(url);

      ws.onopen = () => {
        retriesRef.current = 0;
        setStatus("connected");
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data as string) as ServerMessage;
          setMessages((prev) => [...prev, data]);
        } catch { /* empty */ }
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (intentionalCloseRef.current) {
          setStatus("disconnected");
          return;
        }
        scheduleReconnect();
      };

      ws.onerror = () => {};

      wsRef.current = ws;
    },
    [scheduleReconnect],
  );

  openConnectionRef.current = openConnection;

  const connect = useCallback(
    (callsign: string) => {
      clearReconnectTimer();
      retriesRef.current = 0;
      setMessages([]);
      openConnection(callsign);
    },
    [clearReconnectTimer, openConnection],
  );

  const disconnect = useCallback(() => {
    clearReconnectTimer();
    intentionalCloseRef.current = true;
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  }, [clearReconnectTimer]);

  const reconnect = useCallback(() => {
    clearReconnectTimer();
    retriesRef.current = 0;
    openConnection(callsignRef.current);
  }, [clearReconnectTimer, openConnection]);

  const sendMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    const payload: SendMessagePayload = { action: "sendMessage", text };
    wsRef.current.send(JSON.stringify(payload));
  }, []);

  useEffect(() => {
    return () => {
      clearReconnectTimer();
      intentionalCloseRef.current = true;
      wsRef.current?.close();
    };
  }, [clearReconnectTimer]);

  return { status, messages, sendMessage, connect, disconnect, reconnect };
}
