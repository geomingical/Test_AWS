import type { ServerMessage } from "../types";

interface MessageItemProps {
  message: ServerMessage;
  ownCallsign: string;
}

function formatTime(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function MessageItem({ message, ownCallsign }: MessageItemProps) {
  if (message.type === "system") {
    const verb = message.event === "user_joined" ? "joined" : "left";
    return (
      <div className="message-item message-system">
        <span className="message-system-text">
          {message.callsign} {verb}
        </span>
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>
    );
  }

  const isOwn = message.callsign === ownCallsign;

  return (
    <div className={`message-item ${isOwn ? "message-own" : "message-other"}`}>
      {!isOwn && <span className="message-callsign">{message.callsign}</span>}
      <div className="message-bubble">
        <span className="message-text">{message.text}</span>
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  );
}
