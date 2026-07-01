const isLocalhost = typeof window !== "undefined" &&
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

export const API = isLocalhost
  ? "http://localhost:8000"
  : "https://barbechai-backend.onrender.com";

export const WS_BASE = isLocalhost
  ? "ws://localhost:8000"
  : "wss://barbechai-backend.onrender.com";
