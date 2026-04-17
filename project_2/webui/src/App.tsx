import { useState } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { JoinScreen } from "./components/JoinScreen";
import { ChatScreen } from "./components/ChatScreen";
import "./styles/index.css";

export default function App() {
  const [screen, setScreen] = useState<"join" | "chat">("join");
  const [callsign, setCallsign] = useState("");
  const [joinError, setJoinError] = useState("");
  const { status, messages, sendMessage, connect, reconnect } = useWebSocket();

  const handleJoin = (newCallsign: string) => {
    setJoinError("");
    setCallsign(newCallsign);
    connect(newCallsign);
    setScreen("chat");
  };

  const isConnecting = status === "connecting";

  if (screen === "join") {
    return (
      <JoinScreen
        onJoin={handleJoin}
        isConnecting={isConnecting}
        error={joinError}
      />
    );
  }

  return (
    <ChatScreen
      callsign={callsign}
      messages={messages}
      status={status}
      onSend={sendMessage}
      onReconnect={reconnect}
    />
  );
}
