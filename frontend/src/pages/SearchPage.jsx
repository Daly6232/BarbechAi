import { useState, useRef, useEffect, useCallback } from "react";
import BusinessPopup from "../components/BusinessPopup";
import { TUNISIA_DATA, GOVERNORATES, BUSINESS_TYPES } from "../data/tunisia";

const API = "https://barbechai-backend.onrender.com";

const scoreColor = (s) => s >= 71 ? "#ff4d00" : s >= 41 ? "#f5a623" : "#4a9eff";
const scoreLabel = (s) => s >= 71 ? "HIGH" : s >= 41 ? "MEDIUM" : "LOW";
const tagStyle = (color) => ({ fontFamily: "monospace", fontSize: 9, color, border: `1px solid ${color}33`, padding: "2px 6px", borderRadius: 3, background: `${color}11` });
const labelStyle = { fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 };
const selectStyle = { width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 5, color: "#f0f0f0", padding: "9px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", cursor: "pointer" };

export default function SearchPage() {
  const [governorate, setGovernorate] = useState("Tunis");
  const [city, setCity] = useState("Tunis");
  const [type, setType] = useState("Restaurant");
  const [results, setResults] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));
  const wsRef = useRef(null);
  const enrichedCount = useRef(0);
  const totalCount = useRef(0);
  const progressTimer = useRef(null);

  const cities = TUNISIA_DATA[governorate] || [];

  useEffect(() => { setCity(cities[0] || ""); }, [governorate]);

  const updateProgress = useCallback((label, pct) => {
    setProgressLabel(label);
    setProgress(pct);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(`wss://barbechai-backend.onrender.com/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        if (data.type === "enrichment_update") {
          setResults(prev => prev.map(r =>
            r.id === data.business_id
              ? { ...r, ...data.enrichment, status: "ENRICHED" }
              : r
          ));
          enrichedCount.current += 1;
          if (totalCount.current > 0) {
            const pct = Math.min(95, 50 + Math.round((enrichedCount.current / totalCount.current) * 45));
            updateProgress(`Enrichissement... ${enrichedCount.current}/${totalCount.current}`, pct);
            if (enrichedCount.current >= totalCount.current) {
              updateProgress("Scan terminé ✓", 100);
              setTimeout(() => setScanning(false), 1500);
            }
          }
        }

        if (data.type === "new_discovery") {
          setResults(prev => {
            const exists = prev.find(r => r.name === data.business.name);
            if (exists) return prev.map(r => r.name === data.business.name ? { ...r, ...data.business, is_new_discovery: true } : r);
            totalCount.current += 1;
            return [...prev, { ...data.business, is_new_discovery: true }];
          });
          updateProgress("Nouvelles découvertes...", Math.min(49, progress + 2));
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

    return () => { ws.close(); clearTimeout(progressTimer.current); };
  }, [sessionId]);

  const search = async () => {
    setScanning(true);
    setError(null);
    setResults([]);
    enrichedCount.current = 0;
    totalCount.current = 0;
    updateProgress("Recherche OSM...", 5);

    try {
      const res = await fetch(
        `${API}/discover?city=${encodeURIComponent(city)}&business_type=${encodeURIComponent(type.toLowerCase())}&session_id=${sessionId}`
      );
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      const r = data.results || [];
      setResults(r);
      totalCount.current = r.length;
      enrichedCount.current = 0;

      if (r.length === 0) {
        updateProgress("Recherche via Foursquare, TomTom, Geoapify...", 20);
        progressTimer.current = setTimeout(() => {
          if (scanning) updateProgress("Aucun résultat trouvé", 100);
          setScanning(false);
        }, 30000);
      } else {
        updateProgress(`${r.length} résultats OSM — enrichissement en cours...`, 30);
      }
    } catch (e) {
      setError(e.message);
      setScanning(false);
      updateProgress("", 0);
    }
  };

  const high = results.filter(r => r.score >= 71).length;
  const medium = results.filter(r => r.score >= 41 && r.score < 71).length;
  const low = results.filter(r => r.score < 41).length;
  const enriched = results.filter(r => r.status === "ENRICHED").length;

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "24px 16px" }}>
      {/* Title */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>DISCOVER LEADS</div>
        <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: -1, lineHeight: 1.1 }}>
          Find businesses<br />
          <span style={{ color: "#2a2a2a" }}>missing online presence.</span>
        </h1>
      </div>

      {/* Search Form */}
      <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          <div style={{ flex: 2, minWidth: 160 }}>
            <div style={labelStyle}>Type de commerce</div>
            <select value={type} onChange={e => setType(e.target.value)} style={selectStyle} disabled={scanning}>
              {BUSINESS_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 110 }}>
            <div style={labelStyle}>Gouvernorat</div>
            <select value={governorate} onChange={e => setGovernorate(e.target.value)} style={selectStyle} disabled={scanning}>
              {GOVERNORATES.map(g => <option key={g}>{g}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 110 }}>
            <div style={labelStyle}>Ville</div>
            <select value={city} onChange={e => setCity(e.target.value)} style={selectStyle} disabled={scanning}>
              {cities.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 90 }}>
            <div style={labelStyle}>Pays</div>
            <select style={selectStyle} disabled><option>Tunisie</option></select>
          </div>
        </div>
        <button onClick={search} disabled={scanning} style={{
          width: "100%", background: scanning ? "#1a1a1a" : "#ff4d00",
          color: scanning ? "#444" : "#fff", border: "none", borderRadius: 6,
          padding: "13px", fontSize: 14, fontWeight: 700,
          cursor: scanning ? "not-allowed" : "pointer",
        }}>
          {scanning ? `Scan en cours...` : "Scanner les leads →"}
        </button>

        {/* Progress Bar */}
        {scanning && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444" }}>{progressLabel}</div>
              <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00" }}>{progress}%</div>
            </div>
            <div style={{ height: 4, background: "#1a1a1a", borderRadius: 2, overflow: "hidden" }}>
              <div style={{
                height: "100%", width: `${progress}%`,
                background: progress === 100 ? "#22c55e" : "#ff4d00",
                borderRadius: 2, transition: "width 0.5s ease"
              }} />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: "#1a0a0a", border: "1px solid #ff4d0033", borderRadius: 6, padding: "12px 16px", fontFamily: "monospace", fontSize: 12, color: "#ff4d00", marginBottom: 16 }}>
          ⚠ {error}
        </div>
      )}

      {/* Stats */}
      {results.length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
          {[["HIGH", high, "#ff4d00"], ["MED", medium, "#f5a623"], ["LOW", low, "#4a9eff"], ["TOTAL", results.length, "#555"], ["ENRICHED", enriched, "#22c55e"]].map(([l, v, c]) => (
            <div key={l} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
              <div style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 800, color: c }}>{v}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{l}</div>
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {results.map((biz, i) => (
          <div key={biz.id || i} onClick={() => setSelected(biz)}
            style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderLeft: `3px solid ${scoreColor(biz.score)}`, borderRadius: 6, padding: "14px 18px", cursor: "pointer" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#f0f0f0" }}>{biz.name}</div>
                  {biz.is_new_discovery && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#22c55e", border: "1px solid #22c55e44", padding: "1px 5px", borderRadius: 3 }}>🆕</span>}
                  {biz.has_conflicts && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#f5a623", border: "1px solid #f5a62344", padding: "1px 5px", borderRadius: 3 }}>⚠</span>}
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1, marginBottom: 3 }}>
                  {biz.category?.toUpperCase()} · {biz.city}
                </div>
                {biz.address && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444", marginBottom: 2 }}>📍 {biz.address}</div>}
                {biz.phone && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#4a9eff", marginBottom: 4 }}>📞 {biz.phone}</div>}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 4 }}>
                  {biz.website && <span style={tagStyle("#4a9eff")}>🌐 WEB</span>}
                  {biz.facebook && <span style={tagStyle("#1877f2")}>📘 FB</span>}
                  {biz.instagram && <span style={tagStyle("#e1306c")}>📸 IG</span>}
                  {biz.email && <span style={tagStyle("#22c55e")}>✉ EMAIL</span>}
                  {biz.opening_hours && <span style={tagStyle("#f5a623")}>🕐 HOURS</span>}
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 9, color: biz.status === "ENRICHED" ? "#22c55e" : "#f5a623" }}>
                  {biz.status === "ENRICHED" ? "✓ ENRICHED" : "⟳ ENRICHING..."}
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
