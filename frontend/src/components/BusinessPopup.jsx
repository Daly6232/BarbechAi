import { useState } from "react";

const API = "https://barbechai-backend.onrender.com";

export default function BusinessPopup({ biz, onClose }) {
  const [notes, setNotes] = useState("");
  const [editing, setEditing] = useState(false);
  const [phone, setPhone] = useState(biz.phone || "");
  const [website, setWebsite] = useState(biz.website || "");
  const [facebook, setFacebook] = useState(biz.facebook || "");
  const [instagram, setInstagram] = useState(biz.instagram || "");

  const scoreColor = biz.score >= 71 ? "#ff4d00" : biz.score >= 41 ? "#f5a623" : "#4a9eff";
  const scoreLabel = biz.score >= 71 ? "HIGH" : biz.score >= 41 ? "MEDIUM" : "LOW";

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000cc", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ background: "#0f0f0f", border: "1px solid #2a2a2a", borderRadius: 10, width: "100%", maxWidth: 520, maxHeight: "90vh", overflowY: "auto", padding: 24 }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#f0f0f0", marginBottom: 4 }}>{biz.name}</div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1 }}>{biz.category?.toUpperCase()} · {biz.city}</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ background: scoreColor, color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3 }}>{scoreLabel}</div>
            <div style={{ fontFamily: "monospace", fontSize: 22, fontWeight: 800, color: scoreColor }}>{biz.score}</div>
            <button onClick={onClose} style={{ background: "transparent", border: "1px solid #333", color: "#888", borderRadius: 4, padding: "4px 10px", cursor: "pointer", fontSize: 16 }}>✕</button>
          </div>
        </div>

        {/* Enrichment Status */}
        <div style={{ fontFamily: "monospace", fontSize: 11, color: biz.status === "ENRICHED" ? "#22c55e" : "#f5a623", marginBottom: 16 }}>
          {biz.status === "ENRICHED" ? "✓ FULLY ENRICHED" : "⟳ ENRICHING IN BACKGROUND..."}
        </div>

        {/* Info Fields */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
          <Field label="Address" value={biz.address} editing={editing} />
          <Field label="Phone" value={phone} editing={editing} onChange={setPhone} />
          <Field label="Website" value={website} editing={editing} onChange={setWebsite} isLink />
          <Field label="Facebook" value={facebook} editing={editing} onChange={setFacebook} isLink />
          <Field label="Instagram" value={instagram} editing={editing} onChange={setInstagram} isLink />
        </div>

        {/* Sources Used */}
        {biz.sources_used && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, marginBottom: 6 }}>SOURCES USED</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {biz.sources_used.map(s => (
                <span key={s} style={{ fontFamily: "monospace", fontSize: 10, color: "#22c55e", border: "1px solid #22c55e33", padding: "2px 8px", borderRadius: 3 }}>{s}</span>
              ))}
              {biz.sources_failed?.map(s => (
                <span key={s} style={{ fontFamily: "monospace", fontSize: 10, color: "#ef4444", border: "1px solid #ef444433", padding: "2px 8px", borderRadius: 3 }}>{s} ✕</span>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, marginBottom: 6 }}>NOTES</div>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Add notes about this business..."
            style={{ width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 5, color: "#f0f0f0", padding: "10px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", resize: "vertical", minHeight: 80 }}
          />
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setEditing(!editing)} style={{ flex: 1, background: editing ? "#1e1e1e" : "transparent", border: "1px solid #2a2a2a", color: editing ? "#ff4d00" : "#888", borderRadius: 5, padding: "10px", fontFamily: "monospace", fontSize: 11, cursor: "pointer", letterSpacing: 1 }}>
            {editing ? "SAVE EDITS" : "EDIT INFO"}
          </button>
          <button style={{ flex: 2, background: "#ff4d00", border: "none", color: "#fff", borderRadius: 5, padding: "10px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer", letterSpacing: 1 }}>
            ADD TO CRM →
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, editing, onChange, isLink }) {
  return (
    <div>
      <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, marginBottom: 4 }}>{label}</div>
      {editing && onChange ? (
        <input value={value || ""} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", background: "#080808", border: "1px solid #ff4d0066", borderRadius: 4, color: "#f0f0f0", padding: "7px 10px", fontSize: 13, fontFamily: "Inter, sans-serif" }} />
      ) : (
        <div style={{ fontSize: 13, color: value ? (isLink ? "#4a9eff" : "#f0f0f0") : "#333" }}>
          {isLink && value ? <a href={value} target="_blank" rel="noreferrer" style={{ color: "#4a9eff" }}>{value}</a> : (value || "—")}
        </div>
      )}
    </div>
  );
}
