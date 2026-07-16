import { useState, useEffect } from "react";
import LoginPage from "./pages/LoginPage";
import SearchPage from "./pages/SearchPage";
import LeadsPage from "./pages/LeadsPage";
import CRMPage from "./pages/CRMPage";
import AgentPage from "./pages/AgentPage";
import ExportPage from "./pages/ExportPage";
import UsersPage from "./pages/UsersPage";
// Which tabs each role can see
const ROLE_PAGES = {
  master_admin: ["Search", "Leads", "CRM", "Agent", "Export", "Users"],
  admin: ["Search", "Leads", "CRM", "Agent", "Export", "Users"],
  back_office: ["Leads", "CRM"],
  field_agent: ["Agent"],
};

export default function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [page, setPage] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("barbechai_token");
    const savedUser = localStorage.getItem("barbechai_user");
    if (savedToken && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(parsedUser);
        const pages = ROLE_PAGES[parsedUser.role] || [];
        setPage(pages[0] || null);
      } catch {}
    }
    setChecking(false);
  }, []);

  const handleLogin = (loggedInUser, loggedInToken) => {
    setUser(loggedInUser);
    setToken(loggedInToken);
    const pages = ROLE_PAGES[loggedInUser.role] || [];
    setPage(pages[0] || null);
  };

  const handleLogout = () => {
    localStorage.removeItem("barbechai_token");
    localStorage.removeItem("barbechai_user");
    setUser(null);
    setToken(null);
    setPage(null);
  };

  if (checking) {
    return (
      <div style={{ minHeight: "100vh", background: "#161616", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#444" }}>Chargement...</div>
      </div>
    );
  }

  if (!user || !token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const visiblePages = ROLE_PAGES[user.role] || [];
  const roleLabel = {
    master_admin: "MASTER ADMIN",
    admin: "ADMIN",
    back_office: "BACK OFFICE",
    field_agent: "AGENT TERRAIN",
  }[user.role] || user.role;

  return (
    <div style={{ minHeight: "100vh", background: "#161616", color: "#f0f0f0", fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #1a1a1a", padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 32, height: 32, background: "#ff4d00", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 900, color: "#fff" }}>B</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800 }}>BarbechAI</div>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>TUNISIA BUSINESS INTELLIGENCE</div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 4, flexWrap: "wrap", alignItems: "center" }}>
          {visiblePages.map(p => (
            <button key={p} onClick={() => setPage(p)} style={{
              background: page === p ? "#ff4d00" : "transparent",
              color: page === p ? "#fff" : "#555",
              border: "1px solid " + (page === p ? "#ff4d00" : "#333333"),
              borderRadius: 4, padding: "6px 12px",
              fontFamily: "monospace", fontSize: 11,
              cursor: "pointer", letterSpacing: 1,
            }}>{p.toUpperCase()}</button>
          ))}

          <div style={{ width: 1, height: 20, background: "#333333", margin: "0 6px" }} />

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#f0f0f0" }}>{user.name}</div>
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "#ff4d00", letterSpacing: 1 }}>{roleLabel}</div>
            </div>
            <button onClick={handleLogout} style={{
              background: "transparent", border: "1px solid #333", color: "#888",
              borderRadius: 4, padding: "5px 10px", fontFamily: "monospace", fontSize: 10, cursor: "pointer",
            }}>
              ↪ SORTIR
            </button>
          </div>
        </div>
      </div>

      {/* Pages */}
      {page === "Search" && visiblePages.includes("Search") && <SearchPage />}
      {page === "Leads" && visiblePages.includes("Leads") && <LeadsPage />}
      {page === "CRM" && visiblePages.includes("CRM") && <CRMPage />}
      {page === "Agent" && visiblePages.includes("Agent") && <AgentPage user={user} />}
      {page === "Export" && visiblePages.includes("Export") && <ExportPage />}
      {page === "Users" && visiblePages.includes("Users") && <UsersPage user={user} />}
    </div>
  );
}
