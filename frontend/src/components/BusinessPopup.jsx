import { useState, useEffect } from "react";

import { API } from "../config";

const sourceColors = {
  osm: "#22c55e",
  foursquare: "#4a9eff",
  here: "#f5a623",
  tomtom: "#ef4444",
  geoapify: "#a855f7",
  duckduckgo: "#f97316",
  pagesjaunes: "#ec4899",
  nominatim: "#14b8a6",
  locationiq: "#06b6d4",
  opencage: "#84cc16",
};

export default function BusinessPopup({ biz, onClose }) {
  const [notes, setNotes] = useState("");
  const [editing, setEditing] = useState(false);
  const [phone, setPhone] = useState(biz.phone || "");
  const [website, setWebsite] = useState(biz.website || "");
  const [facebook, setFacebook] = useState(biz.facebook || "");
  const [instagram, setInstagram] = useState(biz.instagram || "");
  const [email, setEmail] = useState(biz.email || "");
  const [address, setAddress] = useState(biz.address || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Sync fields whenever the underlying business data changes
  // (e.g. WebSocket enrichment_update arrives while popup is open)
  useEffect(() => {
    setPhone(biz.phone || "");
    setWebsite(biz.website || "");
    setFacebook(biz.facebook || "");
    setInstagram(biz.instagram || "");
    setEmail(biz.email || "");
    setAddress(biz.address || "");
  }, [biz.id, biz.phone, biz.website, biz.facebook, biz.instagram, biz.email, biz.address]);

  const scoreColor = biz.score >= 71 ? "#ff4d00" : biz.score >= 41 ? "#f5a623" : "#4a9eff";
  const scoreLabel = biz.score >= 71 ? "HIGH" : biz.score >= 41 ? "MEDIUM" : "LOW";

  const sources = biz.sources_used || biz.source || [];
  const sourceList = Array.isArray(sources)
    ? sources
    : typeof sources === "string"
    ? JSON.parse(sources.replace(/'/g, '"'))
    : [];

  const handleSaveToCRM = async () => {
    if (!biz.id) {
      setSaveError("Missing business ID");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const res = await fetch(
        `${API}/crm/add?lead_id=${encodeURIComponent(biz.id)}&notes=${encodeURIComponent(notes)}`,
        { method: "POST" }
      );
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setSaved(true);
      setTimeout(() => { setSaved(false); onClose(); }, 1500);
    } catch (e) {
      setSaveError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000cc", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ background: "#0f0f0f", border: "1px solid #2a2a2a", borderRadius: 10, width: "100%", maxWidth: 540, maxHeight: "90vh", overflowY: "auto", padding: 24 }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#f0f0f0", marginBottom: 4 }}>{biz.name}</div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1 }}>
              {biz.category?.toUpperCase()} · {biz.city}
            </div>
            {biz.is_new_discovery && (
              <span style={{ fontFamily: "monospace", fontSize: 9, color: "#22c55e", border: "1px solid #22c55e44", padding: "1px 6px", borderRadius: 3 }}>🆕 NEW</span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <div style={{ background: scoreColor, color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3 }}>{scoreLabel}</div>
            <div style={{ fontFamily: "monospace", fontSize: 22, fontWeight: 800, color: scoreColor }}>{biz.score}</div>
            <button onClick={onClose} style={{ background: "transparent", border: "1px solid #333", color: "#888", borderRadius: 4, padding: "4px 10px", cursor: "pointer", fontSize: 16 }}>✕</button>
          </div>
        </div>

        {/* Status */}
        <div style={{ fontFamily: "monospace", fontSize: 11, color: biz.status === "ENRICHED" ? "#22c55e" : "#f5a623", marginBottom: 12 }}>
          {biz.status === "ENRICHED" ? "✓ FULLY ENRICHED" : biz.status === "ENRICHING" ? "⟳ ENRICHING..." : `● ${biz.status || "NEW"}`}
        </div>

        {/* Sources */}
        {sourceList.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, marginBottom: 6 }}>DATA SOURCES</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {sourceList.map(s => (
                <span key={s} style={{ fontFamily: "monospace", fontSize: 9, color: sourceColors[s] || "#888", border: `1px solid ${sourceColors[s] || "#888"}33`, padding: "2px 8px", borderRadius: 3 }}>
                  {s.toUpperCase()}
                </span>
              ))}
              {biz.sources_failed?.map(s => (
                <span key={s} style={{ fontFamily: "monospace", fontSize: 9, color: "#ef4444", border: "1px solid #ef444433", padding: "2px 8px", borderRadius: 3 }}>{s} ✕</span>
              ))}
            </div>
          </div>
        )}

        {/* Conflict Warning */}
        {biz.has_conflicts && (
          <div style={{ background: "#1a0a0a", border: "1px solid #f5a62333", borderRadius: 5, padding: "8px 12px", marginBottom: 16, fontFamily: "monospace", fontSize: 10, color: "#f5a623" }}>
            ⚠ Conflicting data detected — review fields marked with ⚠
          </div>
        )}

        {/* Info Fields */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
          <Field label="Address" value={address} editing={editing} onChange={setAddress} conflicted={biz.conflict_fields?.includes("address")} />
          <Field label="Phone" value={phone} editing={editing} onChange={setPhone} conflicted={biz.conflict_fields?.includes("phone")} />
          <Field label="Website" value={website} editing={editing} onChange={setWebsite} isLink conflicted={biz.conflict_fields?.includes("website")} />
          <Field label="Facebook" value={facebook} editing={editing} onChange={setFacebook} isLink conflicted={biz.conflict_fields?.includes("facebook")} />
          <Field label="Instagram" value={instagram} editing={editing} onChange={setInstagram} isLink conflicted={biz.conflict_fields?.includes("instagram")} />
          <Field label="Email" value={email} editing={editing} onChange={setEmail} conflicted={biz.conflict_fields?.includes("email")} />
          {biz.opening_hours && <Field label="Opening Hours" value={biz.opening_hours} editing={false} />}
        </div>

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

        {saveError && (
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#ef4444", marginBottom: 12, background: "#1a0a0a", padding: "8px 12px", borderRadius: 4, border: "1px solid #ef444433" }}>
            {saveError}
          </div>
        )}

        {saved && (
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#22c55e", marginBottom: 12, background: "#0a1a0a", padding: "8px 12px", borderRadius: 4, border: "1px solid #22c55e33" }}>
            ✓ Lead saved to CRM successfully
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setEditing(!editing)} style={{ flex: 1, background: editing ? "#1e1e1e" : "transparent", border: "1px solid #2a2a2a", color: editing ? "#ff4d00" : "#888", borderRadius: 5, padding: "10px", fontFamily: "monospace", fontSize: 11, cursor: "pointer", letterSpacing: 1 }}>
            {editing ? "SAVE EDITS" : "EDIT INFO"}
          </button>
          <button onClick={handleSaveToCRM} disabled={saving || saved} style={{ flex: 2, background: saved ? "#22c55e" : "#ff4d00", border: "none", color: "#fff", borderRadius: 5, padding: "10px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: saving || saved ? "not-allowed" : "pointer", letterSpacing: 1, opacity: saving ? 0.7 : 1 }}>
            {saved ? "✓ SAVED" : saving ? "SAVING..." : "ADD TO CRM →"}
          </button>
        </div>

      </div>
    </div>
  );
}

function Field({ label, value, editing, onChange, isLink, conflicted }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{label}</div>
        {conflicted && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#f5a623" }}>⚠</span>}
      </div>
      {editing && onChange ? (
        <input value={value || ""} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", background: "#080808", border: conflicted ? "1px solid #f5a62366" : "1px solid #ff4d0066", borderRadius: 4, color: "#f0f0f0", padding: "7px 10px", fontSize: 13, fontFamily: "Inter, sans-serif" }} />
      ) : (
        <div style={{ fontSize: 13, color: value ? (isLink ? "#4a9eff" : conflicted ? "#f5a623" : "#f0f0f0") : "#333" }}>
          {isLink && value
            ? <a href={value.startsWith("http") ? value : `https://${value}`} target="_blank" rel="noreferrer" style={{ color: "#4a9eff" }}>{value}</a>
            : (value || "—")}
        </div>
      )}
    </div>
  );
}
