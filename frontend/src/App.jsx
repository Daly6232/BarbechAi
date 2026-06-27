import { useState, useEffect, useRef } from "react";
import SearchPage from "./pages/SearchPage";
import LeadsPage from "./pages/LeadsPage";
import CRMPage from "./pages/CRMPage";
import AgentPage from "./pages/AgentPage";
import ExportPage from "./pages/ExportPage";

const PAGES = ["Search", "Leads", "CRM", "Agent", "Export"];

export default function App() {
  const [page, setPage] = useState("Search");

  return (
    <div style={{ minHeight: "100vh", background: "#080808", color: "#f0f0f0", fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #1a1a1a", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 32, height: 32, background: "#ff4d00", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 900 }}>B</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800 }}>BarbechAI</div>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>TUNISIA BUSINESS INTELLIGENCE</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {PAGES.map(p => (
            <button key={p} onClick={() => setPage(p)} style={{
              background: page === p ? "#ff4d00" : "transparent",
              color: page === p ? "#fff" : "#555",
              border: "1px solid " + (page === p ? "#ff4d00" : "#1e1e1e"),
              borderRadius: 4, padding: "6px 12px",
              fontFamily: "monospace", fontSize: 11,
              cursor: "pointer", letterSpacing: 1,
            }}>{p.toUpperCase()}</button>
          ))}
        </div>
      </div>

      {/* Pages */}
      {page === "Search" && <SearchPage />}
      {page === "Leads" && <LeadsPage />}
      {page === "CRM" && <CRMPage />}
      {page === "Agent" && <AgentPage />}
      {page === "Export" && <ExportPage />}
    </div>
  );
}
