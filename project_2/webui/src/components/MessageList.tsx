import { useEffect, useRef } from "react";
import type { ServerMessage } from "../types";
import { MessageItem } from "./MessageItem";

interface MessageListProps {
  messages: ServerMessage[];
  ownCallsign: string;
}

function messageKey(msg: ServerMessage, idx: number): string {
  return `${msg.timestamp}-${msg.callsign}-${idx}`;
}

export function MessageList({ messages, ownCallsign }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const count = messages.length;

  useEffect(() => {
    if (count > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [count]);

  if (count === 0) {
    return (
      <div className="message-list message-list-empty">
        <p className="empty-text">No messages yet. Say something!</p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg, idx) => (
        <MessageItem key={messageKey(msg, idx)} message={msg} ownCallsign={ownCallsign} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
