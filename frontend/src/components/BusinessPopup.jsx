import { useState } from "react";

const API = "https://barbechai-backend.onrender.com";

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

  const scoreColor = biz.score >= 71 ? "#ff4d00" : biz.score >= 41 ? "#f5a623" : "#4a9eff";
  const scoreLabel = biz.score >= 71 ? "HIGH" : biz.score >= 41 ? "MEDIUM" : "LOW";

  const confidencePct = biz.confidence || 0;
  const confidenceColor = confidencePct >= 70 ? "#22c55e" : confidencePct >= 40 ? "#f5a623" : "#ef4444";

  const handleSaveToCRM = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const payload = {
        business: {
          id: biz.id,
          name: biz.name,
          category: biz.category,
          city: biz.city,
          address: address || biz.address || "",
          lat: biz.lat,
          lng: biz.lng,
          source: JSON.stringify(biz.source || biz.sources_used || ["osm"]),
        },
        score: {
          score: biz.score || 0,
          opportunity_level: scoreLabel,
          has_website: biz.has_website !== undefined ? biz.has_website : !!biz.website,
          has_facebook: biz.has_facebook !== undefined ? biz.has_facebook : !!biz.facebook,
          has_instagram: biz.has_instagram !== undefined ? biz.has_instagram : !!biz.instagram,
          has_phone: biz.has_phone !== undefined ? biz.has_phone : !!biz.phone,
          has_email: biz.has_email !== undefined ? biz.has_email : !!biz.email,
          has_address: biz.has_address !== undefined ? biz.has_address : !!biz.address,
        },
      };

      const res = await fetch(`${API}/crm/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setSaved(true);
      setTimeout(() => {
        setSaved(false);
        onClose();
      }, 1200);
    } catch (e) {
      setSaveError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const sources = biz.sources_used || biz.source || [];
  const sourceList = Array.isArray(sources) ? sources : typeof sources === "string" ? JSON.parse(sources.replace(/'/g, '"')) : [];

  const sourceColors = {
    osm: "#22c55e",
    foursquare: "#4a9eff",
    here: "#f5a623",
    tomtom: "#ef4444",
    geoapify: "#a855f7",
    duckduckgo: "#f97316",
    pagesjaunes: "#ec4899",
    nominatim: "#14b8a6",
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000cc", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ background: "#0f0f0f", border: "1px solid #2a2a2a", borderRadius: 10, width: "100%", maxWidth: 540, maxHeight: "90vh", overflowY: "auto", padding: 24 }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#f0f0f0", marginBottom: 4 }}>{biz.name}</div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1 }}>
              {biz.category?.toUpperCase()} · {biz.city}
            </div>
            {biz.is_new_discovery && (
              <span style={{ fontFamily: "monospace", fontSize: 9, color: "#22c55e", border: "1px solid #22c55e44", padding: "1px 6px", borderRadius: 3, marginLeft: 6 }}>
                🆕 NEW
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ background: scoreColor, color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3 }}>{scoreLabel}</div>
            <div style={{ fontFamily: "monospace", fontSize: 22, fontWeight: 800, color: scoreColor }}>{biz.score}</div>
            <button onClick={onClose} style={{ background: "transparent", border: "1px solid #333", color: "#888", borderRadius: 4, padding: "4px 10px", cursor: "pointer", fontSize: 16 }}>✕</button>
          </div>
        </div>

        {/* Enrichment Status */}
        <div style={{ fontFamily: "monospace", fontSize: 11, color: biz.status === "ENRICHED" ? "#22c55e" : "#f5a623", marginBottom: 12 }}>
          {biz.status === "ENRICHED" ? "✓ FULLY ENRICHED" : biz.status === "ENRICHING" ? "⟳ ENRICHING IN BACKGROUND..." : `● ${biz.status || "NEW"}`}
        </div>

        {/* Confidence Bar */}
        {confidencePct > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>CONFIDENCE</div>
              <div style={{ fontFamily: "monospace", fontSize: 10, fontWeight: 700, color: confidenceColor }}>{confidencePct}%</div>
            </div>
            <div style={{ height: 4, background: "#1a1a1a", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${confidencePct}%`, background: confidenceColor, borderRadius: 2, transition: "width 0.5s" }} />
            </div>
          </div>
        )}

        {/* Source Badges */}
        {sourceList.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, marginBottom: 6 }}>DATA SOURCES</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {sourceList.map(s => (
                <span key={s} style={{
                  fontFamily: "monospace", fontSize: 9, color: sourceColors[s] || "#888",
                  border: `1px solid ${(sourceColors[s] || "#888")}33`,
                  padding: "2px 8px", borderRadius: 3,
                  background: `${(sourceColors[s] || "#888")}11`,
                }}>{s.toUpperCase()}</span>
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

        {/* Error */}
        {saveError && (
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#ef4444", marginBottom: 12, background: "#1a0a0a", padding: "8px 12px", borderRadius: 4, border: "1px solid #ef444433" }}>
            {saveError}
          </div>
        )}

        {/* Success */}
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
          <button
            onClick={handleSaveToCRM}
            disabled={saving || saved}
            style={{
              flex: 2, background: saved ? "#22c55e" : "#ff4d00", border: "none", color: "#fff",
              borderRadius: 5, padding: "10px", fontFamily: "monospace", fontSize: 11,
              fontWeight: 700, cursor: saving || saved ? "not-allowed" : "pointer", letterSpacing: 1,
              opacity: saving ? 0.7 : 1,
            }}
          >
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
        <div style={{ fontSize: 13, color: value ? (isLink ? "#4a9eff" : conflicted ? "#f5a623" : "#f0f0f0") : "#333", textDecoration: conflicted && !value ? "line-through" : "none" }}>
          {isLink && value ? <a href={value.startsWith("http") ? value : `https://${value}`} target="_blank" rel="noreferrer" style={{ color: "#4a9eff" }}>{value}</a> : (value || "—")}
        </div>
      )}
    </div>
  );
}
