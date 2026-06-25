import { useState } from "react";

const API = "https://barbechai-backend.onrender.com";

const TUNISIAN_CITIES = [
  "Tunis", "Sfax", "Sousse", "Kairouan", "Bizerte",
  "Gabès", "Ariana", "Gafsa", "Monastir", "Nabeul",
  "Le Bardo", "La Marsa", "Hammamet", "Djerba"
];

const BUSINESS_TYPES = [
  "restaurant", "cafe", "hotel", "pharmacy", "gym",
  "salon", "supermarket", "clinic", "school", "shop"
];

const scoreColor = (score) => {
  if (score >= 71) return { bg: "#ff4d00", label: "HIGH" };
  if (score >= 41) return { bg: "#f5a623", label: "MEDIUM" };
  return { bg: "#4a9eff", label: "LOW" };
};

const OpportunityBadge = ({ score, opportunity }) => {
  const { bg, label } = scoreColor(score);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{
        background: bg,
        color: "#fff",
        fontFamily: "monospace",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: 2,
        padding: "4px 10px",
        borderRadius: 3,
      }}>{label}</div>
      <div style={{
        fontFamily: "monospace",
        fontSize: 22,
        fontWeight: 800,
        color: bg,
        lineHeight: 1,
      }}>{score}</div>
    </div>
  );
};

const BusinessCard = ({ biz, index }) => {
  const { bg } = scoreColor(biz.score);
  return (
    <div style={{
      background: "#0f0f0f",
      border: "1px solid #1e1e1e",
      borderLeft: `3px solid ${bg}`,
      borderRadius: 6,
      padding: "20px 24px",
      display: "flex",
      flexDirection: "column",
      gap: 12,
      animation: `fadeUp 0.3s ease both`,
      animationDelay: `${index * 0.06}s`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <div style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 16,
            fontWeight: 700,
            color: "#f0f0f0",
            marginBottom: 4,
          }}>{biz.name}</div>
          <div style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "#555",
            textTransform: "uppercase",
            letterSpacing: 1.5,
          }}>{biz.category} · {biz.city}</div>
        </div>
        <OpportunityBadge score={biz.score} opportunity={biz.opportunity} />
      </div>

      {biz.enrichment && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {biz.enrichment.website && (
            <a href={biz.enrichment.website} target="_blank" rel="noreferrer" style={linkStyle("#4a9eff")}>
              🌐 Website
            </a>
          )}
          {biz.enrichment.facebook && (
            <a href={biz.enrichment.facebook} target="_blank" rel="noreferrer" style={linkStyle("#1877f2")}>
              📘 Facebook
            </a>
          )}
          {biz.enrichment.instagram && (
            <a href={biz.enrichment.instagram} target="_blank" rel="noreferrer" style={linkStyle("#e1306c")}>
              📸 Instagram
            </a>
          )}
          {!biz.enrichment.website && !biz.enrichment.facebook && !biz.enrichment.instagram && (
            <span style={{ fontFamily: "monospace", fontSize: 11, color: "#444" }}>No online presence detected</span>
          )}
        </div>
      )}
    </div>
  );
};

const linkStyle = (color) => ({
  fontFamily: "monospace",
  fontSize: 11,
  color,
  textDecoration: "none",
  border: `1px solid ${color}33`,
  padding: "3px 10px",
  borderRadius: 3,
  background: `${color}11`,
});

export default function BarbechAI() {
  const [city, setCity] = useState("Tunis");
  const [type, setType] = useState("restaurant");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState("score");

  const search = async () => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await fetch(`${API}/discover?city=${encodeURIComponent(city)}&business_type=${encodeURIComponent(type)}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResults(data);
    } catch (e) {
      setError(e.message || "Failed to reach BarbechAI backend");
    } finally {
      setLoading(false);
    }
  };

  const sorted = results?.results ? [...results.results].sort((a, b) =>
    sortBy === "score" ? b.score - a.score : a.name.localeCompare(b.name)
  ) : [];

  const stats = results ? {
    high: results.results.filter(r => r.score >= 71).length,
    medium: results.results.filter(r => r.score >= 41 && r.score < 71).length,
    low: results.results.filter(r => r.score < 41).length,
  } : null;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#080808",
      color: "#f0f0f0",
      fontFamily: "'Inter', sans-serif",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; } 50% { opacity: 0.4; }
        }
        select, input { outline: none; }
        select option { background: #1a1a1a; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
      `}</style>

      {/* Header */}
      <div style={{
        borderBottom: "1px solid #1a1a1a",
        padding: "20px 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 36, height: 36,
            background: "#ff4d00",
            borderRadius: 6,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, fontWeight: 900,
          }}>B</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: -0.5 }}>BarbechAI</div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444", letterSpacing: 2 }}>
              TUNISIA BUSINESS INTELLIGENCE
            </div>
          </div>
        </div>
        <div style={{
          fontFamily: "monospace", fontSize: 11,
          color: "#ff4d00", border: "1px solid #ff4d0033",
          padding: "4px 10px", borderRadius: 3,
        }}>● LIVE</div>
      </div>

      {/* Search Panel */}
      <div style={{
        maxWidth: 760,
        margin: "48px auto 0",
        padding: "0 24px",
      }}>
        <div style={{ marginBottom: 36 }}>
          <div style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "#ff4d00",
            letterSpacing: 3,
            marginBottom: 12,
          }}>DISCOVER LEADS</div>
          <h1 style={{
            fontSize: 36,
            fontWeight: 800,
            letterSpacing: -1,
            lineHeight: 1.1,
            color: "#f0f0f0",
          }}>Find businesses<br />
            <span style={{ color: "#333" }}>missing online presence.</span>
          </h1>
        </div>

        {/* Search Controls */}
        <div style={{
          background: "#0f0f0f",
          border: "1px solid #1e1e1e",
          borderRadius: 8,
          padding: 24,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label style={labelStyle}>City</label>
              <select value={city} onChange={e => setCity(e.target.value)} style={selectStyle}>
                {TUNISIAN_CITIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label style={labelStyle}>Business Type</label>
              <select value={type} onChange={e => setType(e.target.value)} style={selectStyle}>
                {BUSINESS_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={search}
            disabled={loading}
            style={{
              background: loading ? "#1a1a1a" : "#ff4d00",
              color: loading ? "#444" : "#fff",
              border: "none",
              borderRadius: 6,
              padding: "14px 28px",
              fontSize: 14,
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              letterSpacing: 0.5,
              transition: "background 0.2s",
            }}
          >
            {loading ? "Scanning..." : "Scan for Leads →"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            marginTop: 24,
            background: "#1a0a0a",
            border: "1px solid #ff4d0033",
            borderRadius: 6,
            padding: "14px 18px",
            fontFamily: "monospace",
            fontSize: 13,
            color: "#ff4d00",
          }}>⚠ {error}</div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ marginTop: 48, textAlign: "center" }}>
            <div style={{
              fontFamily: "monospace",
              fontSize: 13,
              color: "#444",
              animation: "pulse 1.4s ease infinite",
              letterSpacing: 2,
            }}>SCANNING {city.toUpperCase()} FOR {type.toUpperCase()}S...</div>
          </div>
        )}

        {/* Stats Bar */}
        {stats && (
          <div style={{
            marginTop: 32,
            display: "flex",
            gap: 12,
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div style={{ display: "flex", gap: 12 }}>
              <Stat label="HIGH" value={stats.high} color="#ff4d00" />
              <Stat label="MED" value={stats.medium} color="#f5a623" />
              <Stat label="LOW" value={stats.low} color="#4a9eff" />
              <Stat label="TOTAL" value={results.count} color="#555" />
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontFamily: "monospace", fontSize: 11, color: "#444" }}>SORT</span>
              {["score", "name"].map(s => (
                <button key={s} onClick={() => setSortBy(s)} style={{
                  background: sortBy === s ? "#1e1e1e" : "transparent",
                  border: "1px solid #1e1e1e",
                  color: sortBy === s ? "#f0f0f0" : "#555",
                  fontFamily: "monospace",
                  fontSize: 11,
                  padding: "4px 10px",
                  borderRadius: 3,
                  cursor: "pointer",
                  textTransform: "uppercase",
                  letterSpacing: 1,
                }}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {sorted.length > 0 && (
          <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 10, paddingBottom: 60 }}>
            {sorted.map((biz, i) => (
              <BusinessCard key={i} biz={biz} index={i} />
            ))}
          </div>
        )}

        {results && results.count === 0 && (
          <div style={{
            marginTop: 48,
            textAlign: "center",
            fontFamily: "monospace",
            fontSize: 13,
            color: "#333",
          }}>No businesses found for this search. Try a different city or type.</div>
        )}
      </div>
    </div>
  );
}

const labelStyle = {
  display: "block",
  fontFamily: "monospace",
  fontSize: 10,
  color: "#444",
  letterSpacing: 2,
  textTransform: "uppercase",
  marginBottom: 8,
};

const selectStyle = {
  width: "100%",
  background: "#080808",
  border: "1px solid #2a2a2a",
  borderRadius: 5,
  color: "#f0f0f0",
  padding: "10px 14px",
  fontSize: 14,
  fontFamily: "'Inter', sans-serif",
  cursor: "pointer",
};

const Stat = ({ label, value, color }) => (
  <div style={{
    background: "#0f0f0f",
    border: "1px solid #1e1e1e",
    borderRadius: 4,
    padding: "6px 14px",
    textAlign: "center",
  }}>
    <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color }}>{value}</div>
    <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{label}</div>
  </div>
);

