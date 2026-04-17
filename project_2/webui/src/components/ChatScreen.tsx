import type { ConnectionStatus, ServerMessage } from "../types";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { StatusIndicator } from "./StatusIndicator";

interface ChatScreenProps {
  callsign: string;
  messages: ServerMessage[];
  status: ConnectionStatus;
  onSend: (text: string) => void;
  onReconnect: () => void;
}

export function ChatScreen({
  callsign,
  messages,
  status,
  onSend,
  onReconnect,
}: ChatScreenProps) {
  const isDisconnected = status !== "connected";

  return (
    <div className="chat-screen">
      <header className="chat-header">
        <h1 className="chat-title">Anonymous Chat</h1>
        <div className="chat-header-right">
          <span className="chat-callsign">{callsign}</span>
          <StatusIndicator status={status} onReconnect={onReconnect} />
        </div>
      </header>

      <MessageList messages={messages} ownCallsign={callsign} />

      <footer className="chat-footer">
        <MessageInput onSend={onSend} disabled={isDisconnected} />
      </footer>
    </div>
  );
}
