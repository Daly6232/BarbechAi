// Capacitor's WebView serves the bundled app from https://localhost internally
// on Android — that's not "local dev", it's the packaged app running for real.
// window.Capacitor only exists inside the native wrapper, so check that first;
// only fall back to hostname sniffing when running as an actual browser tab.
const isNativeApp = typeof window !== "undefined" && !!window.Capacitor?.isNativePlatform?.();

const isLocalhost = !isNativeApp && typeof window !== "undefined" &&
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

export const API = isLocalhost
  ? "http://localhost:8000"
  : "https://barbechai.onrender.com";

export const WS_BASE = isLocalhost
  ? "ws://localhost:8000"
  : "wss://barbechai.onrender.com";
