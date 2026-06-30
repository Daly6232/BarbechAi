// Toggle this to switch between local testing and production
const USE_LOCAL = true;

export const API = USE_LOCAL
  ? "http://localhost:8000"
  : "https://barbechai-backend.onrender.com";

export const WS_BASE = USE_LOCAL
  ? "ws://localhost:8000"
  : "wss://barbechai-backend.onrender.com";
