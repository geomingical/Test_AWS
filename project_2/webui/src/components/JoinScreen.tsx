import { useState } from "react";
import { CALLSIGN_MAX_LENGTH, CALLSIGN_PATTERN } from "../config";

interface JoinScreenProps {
  onJoin: (callsign: string) => void;
  isConnecting: boolean;
  error: string;
}

export function JoinScreen({ onJoin, isConnecting, error }: JoinScreenProps) {
  const [callsign, setCallsign] = useState("");
  const [validationError, setValidationError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const trimmed = callsign.trim();
    if (!trimmed) {
      setValidationError("Callsign is required");
      return;
    }
    if (!CALLSIGN_PATTERN.test(trimmed)) {
      setValidationError("Only letters, numbers, and underscores (1–20 chars)");
      return;
    }

    setValidationError("");
    onJoin(trimmed);
  };

  const displayError = validationError || error;

  return (
    <div className="join-screen">
      <div className="join-card">
        <h1 className="join-title">Anonymous Chat</h1>
        <p className="join-subtitle">Enter a callsign to join the room</p>

        <form onSubmit={handleSubmit} className="join-form">
          <label htmlFor="callsign-input" className="sr-only">
            Callsign
          </label>
          <input
            id="callsign-input"
            type="text"
            className="join-input"
            placeholder="Your callsign"
            value={callsign}
            onChange={(e) => {
              setCallsign(e.target.value);
              setValidationError("");
            }}
            maxLength={CALLSIGN_MAX_LENGTH}
            disabled={isConnecting}
            autoComplete="off"
          />
          {displayError && (
            <p className="join-error" role="alert">
              {displayError}
            </p>
          )}
          <button
            type="submit"
            className="join-button"
            disabled={isConnecting || !callsign.trim()}
          >
            {isConnecting ? "Connecting…" : "Join Chat"}
          </button>
        </form>
      </div>
    </div>
  );
}
