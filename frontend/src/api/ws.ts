import { getToken } from "@/auth/session";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://127.0.0.1:8000/ws/stream";

interface WsHandlers {
  onMessage: (payload: unknown) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: () => void;
}

export function createStreamSocket({ onMessage, onOpen, onClose, onError }: WsHandlers): WebSocket {
  const token = encodeURIComponent(getToken());
  const wsUrl = `${WS_URL}${WS_URL.includes("?") ? "&" : "?"}token=${token}`;
  const socket = new WebSocket(wsUrl);
  socket.onopen = () => onOpen?.();
  socket.onclose = () => onClose?.();
  socket.onerror = () => onError?.();
  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      onMessage(event.data);
    }
  };
  return socket;
}
