// websocket.js
// Handles the live connection to the CipherZenith backend dashboard channel.
// Backend contract (fixed — do not change without telling the team):
// ws://localhost:8000/ws/dashboard
// Message shape: { step, title, status, details, timestamp }

const WS_URL = import.meta.env?.VITE_DASHBOARD_WS_URL || "ws://localhost:8000/ws/dashboard";

const RECONNECT_BASE_DELAY_MS = 1000;
const RECONNECT_MAX_DELAY_MS = 15000;

/**
 * Creates a managed WebSocket connection with auto-reconnect and
 * basic message validation (see security/auth_guard.js for the
 * shape-checking logic reused here).
 *
 * @param {Object} handlers
 * @param {(msg: object) => void} handlers.onStepUpdate
 * @param {() => void} [handlers.onOpen]
 * @param {() => void} [handlers.onClose]
 * @param {(err: Event) => void} [handlers.onError]
 * @returns {{ close: () => void, getStatus: () => string }}
 */
export function connectDashboardSocket({ onStepUpdate, onOpen, onClose, onError }) {
  let socket = null;
  let reconnectAttempts = 0;
  let manuallyClosed = false;
  let status = "connecting";

  function scheduleReconnect() {
    if (manuallyClosed) return;
    const delay = Math.min(
      RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempts,
      RECONNECT_MAX_DELAY_MS
    );
    reconnectAttempts += 1;
    setTimeout(open, delay);
  }

  function open() {
    status = "connecting";
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      status = "connected";
      reconnectAttempts = 0;
      onOpen?.();
    };

    socket.onmessage = (event) => {
      const parsed = safeParseStepMessage(event.data);
      if (!parsed.valid) {
        console.warn("[websocket] dropped malformed dashboard message:", parsed.reason);
        return;
      }
      onStepUpdate(parsed.data);
    };

    socket.onclose = () => {
      status = "disconnected";
      onClose?.();
      scheduleReconnect();
    };

    socket.onerror = (err) => {
      status = "error";
      onError?.(err);
      // onclose will fire right after; reconnect is handled there
    };
  }

  open();

  return {
    close: () => {
      manuallyClosed = true;
      socket?.close();
    },
    getStatus: () => status,
  };
}

/**
 * Validates and parses an incoming dashboard message.
 * Never trust raw socket input — this is the frontend's first line
 * of defense against a malformed or malicious payload.
 */
function safeParseStepMessage(raw) {
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return { valid: false, reason: "not valid JSON" };
  }

  const VALID_STATUSES = ["processing", "complete", "threat_detected"];

  if (typeof data.step !== "number" || data.step < 1 || data.step > 8) {
    return { valid: false, reason: "step must be a number 1-8" };
  }
  if (typeof data.title !== "string" || data.title.length === 0 || data.title.length > 100) {
    return { valid: false, reason: "title missing or too long" };
  }
  if (!VALID_STATUSES.includes(data.status)) {
    return { valid: false, reason: "unknown status value" };
  }
  if (typeof data.details !== "object" || data.details === null) {
    return { valid: false, reason: "details must be an object" };
  }
  if (typeof data.timestamp !== "string") {
    return { valid: false, reason: "timestamp missing" };
  }

  return { valid: true, data };
}