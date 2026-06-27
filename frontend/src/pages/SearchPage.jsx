import { useState, useRef, useEffect } from "react";
import BusinessPopup from "../components/BusinessPopup";
import { TUNISIA_DATA, GOVERNORATES, BUSINESS_TYPES } from "../data/tunisia";

const API = "https://barbechai-backend.onrender.com";

const scoreColor = (score) => score >= 71 ? "#ff4d00" : score >= 41 ? "#f5a623" : "#4a9eff";
const scoreLabel = (score) => score >= 71 ? "HIGH" : score >= 41 ? "MEDIUM" : "LOW";

export default function SearchPage() {
  const [governorate, setGovernorate] = useState("Tunis");
  const [city, setCity] = useState("Tunis");
  const [type, setType] = useState("Restaurant");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));
  const wsRef = useRef(null);

  const cities = TUNISIA_DATA[governorate] || [];

  useEffect(() => {
    setCity(cities[0] || "");
  }, [governorate]);

  useEffect(() => {
    const ws = new WebSocket(`wss://barbechai-backend.onrender.com/ws/${sessionId}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        if (data.type === "enrichment_update") {
          setResults(prev => prev.map(r =>
            r.id === data.business_id
              ? { ...r, ...data.enrichment, status: data.enrichment.status || "ENRICHED" }
              : r
          ));
        }

        if (data.type === "new_discovery") {
          setResults(prev => {
            const exists = prev.find(r => r.id === data.business.id);
            if (exists) {
              return prev.map(r =>
                r.id === data.business.id
                  ? { ...r, ...data.business, is_new_discovery: true }
                  : r
              );
            }
            return [...prev, { ...data.business, is_new_discovery: true }];
          });
        }

        if (data.type === "confidence_update") {
          setResults(prev => prev.map(r =>
            r.id === data.business_id
              ? { ...r, confidence: data.confidence, sources_used: data.sources_used }
              : r
          ));
        }

        if (data.type === "conflict_detected") {
          setResults(prev => prev.map(r =>
            r.id === data.business_id
              ? { ...r, has_conflicts: true, conflict_fields: data.conflict_fields || [] }
              : r
          ));
        }
      } catch {}
    };
    return () => ws.close();
  }, [sessionId]);

  const search = async () => {
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const res = await fetch(`${API}/discover?city=${encodeURIComponent(city)}&business_type=${encodeURIComponent(type.toLowerCase())}&session_id=${sessionId}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResults(data.results || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const high = results.filter(r => r.score >= 71).length;
  const medium = results.filter(r => r.score >= 41 && r.score < 71).length;
  const low = results.filter(r => r.score < 41).length;
  const newDiscoveries = results.filter(r => r.is_new_discovery).length;

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "24px 16px" }}>
      {/* Title */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>DISCOVER LEADS</div>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: -1, lineHeight: 1.1 }}>
          Find businesses<br />
          <span style={{ color: "#2a2a2a" }}>missing online presence.</span>
        </h1>
      </div>

      {/* Search Form */}
      <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 8, padding: 16, marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          <div style={{ flex: 2, minWidth: 160 }}>
            <div style={labelStyle}>Business Type</div>
            <select value={type} onChange={e => setType(e.target.value)} style={selectStyle}>
              {BUSINESS_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 120 }}>
            <div style={labelStyle}>Governorate</div>
            <select value={governorate} onChange={e => setGovernorate(e.target.value)} style={selectStyle}>
              {GOVERNORATES.map(g => <option key={g}>{g}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 120 }}>
            <div style={labelStyle}>City</div>
            <select value={city} onChange={e => setCity(e.target.value)} style={selectStyle}>
              {cities.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 90 }}>
            <div style={labelStyle}>Country</div>
            <select style={selectStyle} disabled>
              <option>Tunisia</option>
            </select>
          </div>
        </div>
        <button onClick={search} disabled={loading} style={{
          width: "100%", background: loading ? "#1a1a1a" : "#ff4d00",
          color: loading ? "#444" : "#fff", border: "none", borderRadius: 6,
          padding: "13px", fontSize: 14, fontWeight: 700,
          cursor: loading ? "not-allowed" : "pointer",
        }}>
          {loading ? `Scanning ${city}...` : "Scan for Leads →"}
        </button>
      </div>

      {error && (
        <div style={{ background: "#1a0a0a", border: "1px solid #ff4d0033", borderRadius: 6, padding: "12px 16px", fontFamily: "monospace", fontSize: 12, color: "#ff4d00", marginBottom: 16 }}>
          ⚠ {error}
        </div>
      )}

      {/* Stats */}
      {results.length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
          {[["HIGH", high, "#ff4d00"], ["MED", medium, "#f5a623"], ["LOW", low, "#4a9eff"], ["TOTAL", results.length, "#555"]].map(([l, v, c]) => (
            <div key={l} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
              <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: c }}>{v}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{l}</div>
            </div>
          ))}
          {newDiscoveries > 0 && (
            <div key="new" style={{ background: "#0f0f0f", border: "1px solid #22c55e33", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
              <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: "#22c55e" }}>{newDiscoveries}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#22c55e", letterSpacing: 2 }}>NEW</div>
            </div>
          )}
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444", alignSelf: "center", marginLeft: 8 }}>
            {results.filter(r => r.status === "ENRICHED").length}/{results.length} enriched
          </div>
        </div>
      )}

      {/* Results */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {results.map((biz, i) => (
          <div key={biz.id || i} onClick={() => setSelected(biz)}
            style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderLeft: `3px solid ${scoreColor(biz.score)}`, borderRadius: 6, padding: "14px 18px", cursor: "pointer" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                {/* Name + Badges */}
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: "#f0f0f0" }}>{biz.name}</span>
                  {biz.is_new_discovery && (
                    <span style={{ fontFamily: "monospace", fontSize: 9, color: "#22c55e", border: "1px solid #22c55e44", padding: "1px 5px", borderRadius: 3 }}>
                      🆕
                    </span>
                  )}
                  {biz.has_conflicts && (
                    <span style={{ fontFamily: "monospace", fontSize: 9, color: "#f5a623", border: "1px solid #f5a62344", padding: "1px 5px", borderRadius: 3 }}>
                      ⚠
                    </span>
                  )}
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1, marginBottom: 4 }}>
                  {biz.category?.toUpperCase()} · {biz.city}
                </div>
                {biz.address && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444", marginBottom: 2 }}>📍 {biz.address}</div>}
                {biz.phone && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#4a9eff", marginBottom: 4 }}>📞 {biz.phone}</div>}

                {/* ── SOCIAL MATRIX ── */}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 6, marginTop: 2 }}>
                  <SocialBadge
                    icon="🌐"
                    label="WWW"
                    present={!!biz.website}
                    color="#4a9eff"
                  />
                  <SocialBadge
                    icon="📘"
                    label="FB"
                    present={!!biz.facebook}
                    color="#1877f2"
                  />
                  <SocialBadge
                    icon="📸"
                    label="IG"
                    present={!!biz.instagram}
                    color="#e1306c"
                  />
                  <SocialBadge
                    icon="✉"
                    label="EMAIL"
                    present={!!biz.email}
                    color="#22c55e"
                  />
                </div>

                {/* Status + Confidence */}
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{ fontFamily: "monospace", fontSize: 9, color: biz.status === "ENRICHED" ? "#22c55e" : biz.status === "ENRICHING" ? "#f5a623" : "#4a9eff" }}>
                    {biz.status === "ENRICHED" ? "✓ ENRICHED" : biz.status === "ENRICHING" ? "⟳ ENRICHING..." : `● ${biz.status || "NEW"}`}
                  </div>
                  {biz.confidence > 0 && (
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <div style={{ width: 40, height: 3, background: "#1a1a1a", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ height: "100%", width: `${biz.confidence}%`, background: biz.confidence >= 70 ? "#22c55e" : biz.confidence >= 40 ? "#f5a623" : "#ef4444", borderRadius: 2 }} />
                      </div>
                      <span style={{ fontFamily: "monospace", fontSize: 8, color: "#444" }}>{biz.confidence}%</span>
                    </div>
                  )}
                </div>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 12 }}>
                <div style={{ background: scoreColor(biz.score), color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3, marginBottom: 4 }}>
                  {scoreLabel(biz.score)}
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 20, fontWeight: 800, color: scoreColor(biz.score) }}>
                  {biz.score}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function SocialBadge({ icon, label, present, color }) {
  return (
    <span style={{
      fontFamily: "monospace",
      fontSize: 9,
      color: present ? color : "#333",
      border: `1px solid ${present ? color + "44" : "#1a1a1a"}`,
      padding: "2px 6px",
      borderRadius: 3,
      background: present ? color + "11" : "transparent",
      textDecoration: present ? "none" : "line-through",
      opacity: present ? 1 : 0.5,
    }}>
      {icon} {label}
    </span>
  );
}

const labelStyle = { fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 };
const selectStyle = { width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 5, color: "#f0f0f0", padding: "9px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", cursor: "pointer" };
