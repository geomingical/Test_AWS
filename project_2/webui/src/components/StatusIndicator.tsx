import type { ConnectionStatus } from "../types";

const STATUS_CONFIG: Record<
  ConnectionStatus,
  { label: string; className: string }
> = {
  idle: { label: "Not connected", className: "status-idle" },
  connecting: { label: "Connecting…", className: "status-connecting" },
  connected: { label: "Connected", className: "status-connected" },
  disconnected: { label: "Disconnected", className: "status-disconnected" },
  reconnecting: { label: "Reconnecting…", className: "status-reconnecting" },
};

interface StatusIndicatorProps {
  status: ConnectionStatus;
  onReconnect?: () => void;
}

export function StatusIndicator({ status, onReconnect }: StatusIndicatorProps) {
  const { label, className } = STATUS_CONFIG[status];

  return (
    <div className={`status-indicator ${className}`} aria-live="polite">
      <span className="status-dot" />
      <span className="status-label">{label}</span>
      {status === "disconnected" && onReconnect && (
        <button type="button" className="reconnect-button" onClick={onReconnect}>
          Reconnect
        </button>
      )}
    </div>
  );
}
