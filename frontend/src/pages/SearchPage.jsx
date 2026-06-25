import { useState, useRef, useEffect } from "react";
import BusinessPopup from "../components/BusinessPopup";

const API = "https://barbechai-backend.onrender.com";

const CITIES = ["Tunis","Sfax","Sousse","Kairouan","Bizerte","Gabès","Ariana","Gafsa","Monastir","Nabeul","Le Bardo","La Marsa","Hammamet","Djerba","Zarzis","Ben Arous","Manouba","Zaghouan","Béja","Jendouba","Kef","Siliana","Mahdia","Sidi Bouzid","Kasserine","Gafsa","Tozeur","Kebili","Medenine","Tataouine"];

const GOVERNORATES = ["Tunis","Ariana","Ben Arous","Manouba","Nabeul","Zaghouan","Bizerte","Béja","Jendouba","Kef","Siliana","Sousse","Monastir","Mahdia","Sfax","Kairouan","Kasserine","Sidi Bouzid","Gabès","Medenine","Tataouine","Gafsa","Tozeur","Kebili"];

const BUSINESS_TYPES = ["Restaurant","Café","Hotel","Pharmacy","Gym","Salon","Supermarket","Clinic","School","Shop","Bakery","Butcher","Bank","Insurance","Real Estate","Law Firm","Accounting","Dentist","Doctor","Veterinary","Optical","Jewelry","Clothing","Electronics","Furniture","Auto Repair","Car Wash","Gas Station","Travel Agency","Wedding Hall","Photography","Printing","Construction","Architecture","Cleaning Service","Security","Transport","Logistics","Wholesale","Factory","Mosque","Church","Association","Hammam","Spa","Nightclub","Cinema","Theater","Museum","Library","Kindergarten","University","Training Center","Language School","IT Company","Marketing Agency","Advertising","Catering","Florist","Toy Store","Book Store","Sports Club","Swimming Pool","Coworking Space"];

const scoreColor = (score) => {
  if (score >= 71) return "#ff4d00";
  if (score >= 41) return "#f5a623";
  return "#4a9eff";
};

const scoreLabel = (score) => {
  if (score >= 71) return "HIGH";
  if (score >= 41) return "MEDIUM";
  return "LOW";
};

export default function SearchPage() {
  const [city, setCity] = useState("Tunis");
  const [governorate, setGovernorate] = useState("Tunis");
  const [type, setType] = useState("Restaurant");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`wss://barbechai-backend.onrender.com/ws/${sessionId}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "enrichment_update") {
        setResults(prev => prev.map(r =>
          r.id === data.business_id ? { ...r, ...data.enrichment, status: "ENRICHED" } : r
        ));
      }
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

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 16px" }}>
      {/* Title */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 10 }}>DISCOVER LEADS</div>
        <h1 style={{ fontSize: 32, fontWeight: 800, letterSpacing: -1, lineHeight: 1.1 }}>
          Find businesses<br />
          <span style={{ color: "#2a2a2a" }}>missing online presence.</span>
        </h1>
      </div>

      {/* Search Form */}
      <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 8, padding: 20, marginBottom: 24 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
          <div style={{ flex: 1, minWidth: 140 }}>
            <div style={labelStyle}>Business Type</div>
            <select value={type} onChange={e => setType(e.target.value)} style={selectStyle}>
              {BUSINESS_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 120 }}>
            <div style={labelStyle}>City</div>
            <select value={city} onChange={e => setCity(e.target.value)} style={selectStyle}>
              {CITIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 120 }}>
            <div style={labelStyle}>Governorate</div>
            <select value={governorate} onChange={e => setGovernorate(e.target.value)} style={selectStyle}>
              {GOVERNORATES.map(g => <option key={g}>{g}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 100 }}>
            <div style={labelStyle}>Country</div>
            <select style={selectStyle} disabled>
              <option>Tunisia</option>
            </select>
          </div>
        </div>
        <button onClick={search} disabled={loading} style={{
          width: "100%", background: loading ? "#1a1a1a" : "#ff4d00",
          color: loading ? "#444" : "#fff", border: "none", borderRadius: 6,
          padding: "13px", fontSize: 14, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
        }}>
          {loading ? "Scanning..." : "Scan for Leads →"}
        </button>
      </div>

      {error && <div style={{ background: "#1a0a0a", border: "1px solid #ff4d0033", borderRadius: 6, padding: "12px 16px", fontFamily: "monospace", fontSize: 12, color: "#ff4d00", marginBottom: 16 }}>⚠ {error}</div>}

      {/* Stats */}
      {results.length > 0 && (
        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          {[["HIGH", high, "#ff4d00"], ["MED", medium, "#f5a623"], ["LOW", low, "#4a9eff"], ["TOTAL", results.length, "#555"]].map(([l, v, c]) => (
            <div key={l} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
              <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: c }}>{v}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{l}</div>
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {results.map((biz, i) => (
          <div key={biz.id || i} onClick={() => setSelected(biz)}
            style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderLeft: `3px solid ${scoreColor(biz.score)}`, borderRadius: 6, padding: "16px 20px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#f0f0f0", marginBottom: 3 }}>{biz.name}</div>
              <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1 }}>{biz.category?.toUpperCase()} · {biz.city}</div>
              <div style={{ fontFamily: "monospace", fontSize: 10, marginTop: 4, color: biz.status === "ENRICHED" ? "#22c55e" : "#f5a623" }}>
                {biz.status === "ENRICHED" ? "✓ ENRICHED" : "⟳ ENRICHING..."}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ background: scoreColor(biz.score), color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3, marginBottom: 4 }}>{scoreLabel(biz.score)}</div>
              <div style={{ fontFamily: "monospace", fontSize: 22, fontWeight: 800, color: scoreColor(biz.score) }}>{biz.score}</div>
            </div>
          </div>
        ))}
      </div>

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

const labelStyle = { fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 };
const selectStyle = { width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 5, color: "#f0f0f0", padding: "9px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", cursor: "pointer" };
