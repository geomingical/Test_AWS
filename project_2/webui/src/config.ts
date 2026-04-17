export const WS_ENDPOINT =
  import.meta.env.VITE_WS_ENDPOINT ||
  "wss://ezi50tf1w1.execute-api.ap-northeast-1.amazonaws.com/prod";

export const CALLSIGN_PATTERN = /^[a-zA-Z0-9_]{1,20}$/;
export const CALLSIGN_MAX_LENGTH = 20;
export const MESSAGE_MAX_LENGTH = 1000;

export const RECONNECT_BASE_DELAY_MS = 2000;
export const RECONNECT_MAX_DELAY_MS = 30000;
export const RECONNECT_MAX_ATTEMPTS = 5;
