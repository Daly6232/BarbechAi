import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import { API } from "../config";

const ACTION_LABELS = {
  CONTACTED: "Contacté",
  NO_ANSWER: "Pas de réponse",
  CALLBACK: "Rappel demandé",
  INTERESTED: "Intéressé",
  NOT_INTERESTED: "Pas intéressé",
  DEAL_CLOSED: "Deal conclu",
  DECLINED: "Refusé",
};

function actionLabel(action) {
  if (!action) return "Action";
  if (action.startsWith("UPDATE:")) {
    const fields = action.replace("UPDATE:", "");
    return fields === "noop" ? "Mise à jour" : `Mise à jour: ${fields.replace(/,/g, ", ")}`;
  }
  return ACTION_LABELS[action] || action;
}

export default function AgentTimelineModal({ agent, onClose }) {
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiFetch(`${API}/agent/${encodeURIComponent(agent.id)}/timeline`)
      .then(r => r.json())
      .then(d => { if (!cancelled) setActivity(d.activity || []); })
      .catch(() => { if (!cancelled) setActivity([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [agent.id]);

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000cc", zIndex: 1000, display: "flex", alignItems: "flex-end", justifyContent: "center" }} onClick={onClose}>
      <div
        style={{ background: "#FFFFFF", borderRadius: "14px 14px 0 0", width: "100%", maxWidth: 560, maxHeight: "85vh", overflowY: "auto", padding: 20 }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 17, fontWeight: 800, color: "#121830" }}>{agent.name}</div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#C4A264", letterSpacing: 1, marginTop: 2 }}>
              HISTORIQUE COMPLET
            </div>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#9AA0AC", fontSize: 20, cursor: "pointer", lineHeight: 1 }}>✕</button>
        </div>

        {loading ? (
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Chargement...</div>
        ) : activity.length === 0 ? (
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Aucune activité enregistrée pour cet agent.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {activity.map(item => (
              <div key={item.id} style={{ borderLeft: "2px solid #C4A264", paddingLeft: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "#121830" }}>{actionLabel(item.action)}</div>
                <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", marginTop: 2 }}>
                  {item.lead_name || "Lead"} · {item.timestamp ? new Date(item.timestamp).toLocaleString() : ""}
                </div>
                {item.notes && (
                  <div style={{ fontSize: 12, color: "#374151", marginTop: 4 }}>{item.notes}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
