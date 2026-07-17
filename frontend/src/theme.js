// ZAYER Digital brand palette, sampled from the company logo.
// Centralized here so every page pulls from one source instead of
// re-declaring hex codes (which is how the old dark/orange theme drifted
// out of sync with the brand in the first place).
export const theme = {
  bg: "#F5F6F8",        // app background
  card: "#FFFFFF",      // panels/cards
  border: "#E2E4E9",    // standard border
  borderStrong: "#D7DAE1",
  divider: "#E5E7EB",
  navy: "#121830",       // primary brand color (was #ff4d00 orange)
  navySoft: "#2A3050",
  gold: "#C4A264",       // accent only — logo dot, small highlights
  goldSoft: "#FBF3E7",   // light gold tint for notices
  goldText: "#8A6D2F",
  text: "#121830",       // primary text (was #f0f0f0)
  textMuted: "#6B7280",  // secondary/label text (was #555/#444/#666/#ccc)
  textFaint: "#9AA0AC",  // faint/placeholder text (was #333/#222)
  white: "#FFFFFF",
  success: "#22c55e",
  successSoft: "#EAFBF1",
  danger: "#ef4444",
  dangerSoft: "#FDEDED",
  warning: "#f5a623",
  info: "#4a9eff",
  purple: "#a855f7",
};
