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

export default function LeadActivityModal({ lead, onClose, onNoteAdded }) {
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState("");
  const [savingNote, setSavingNote] = useState(false);

  const fetchActivity = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${API}/crm/lead/${encodeURIComponent(lead.id)}/activity`);
      const data = await res.json();
      setActivity(data.activity || []);
    } catch {
      setActivity([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchActivity(); }, [lead.id]);

  const submitNote = async () => {
    if (!note.trim()) return;
    setSavingNote(true);
    try {
      await apiFetch(`${API}/crm/note?lead_id=${encodeURIComponent(lead.id)}&note=${encodeURIComponent(note)}`, { method: "POST" });
      setNote("");
      onNoteAdded?.();
      // Notes added this way don't create an AgentActivity row (that's a
      // separate table), so we don't need to refetch activity here — just
      // let the parent refresh the lead's crm_notes.
    } catch {} finally {
      setSavingNote(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000cc", zIndex: 1000, display: "flex", alignItems: "flex-end", justifyContent: "center" }} onClick={onClose}>
      <div
        style={{ background: "#FFFFFF", borderRadius: "14px 14px 0 0", width: "100%", maxWidth: 560, maxHeight: "85vh", overflowY: "auto", padding: 20 }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
          <div>
            <div style={{ fontSize: 17, fontWeight: 800, color: "#121830" }}>{lead.name}</div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", letterSpacing: 1, marginTop: 2 }}>
              {lead.category?.toUpperCase()} · {lead.city}
            </div>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#9AA0AC", fontSize: 20, cursor: "pointer", lineHeight: 1 }}>✕</button>
        </div>

        {lead.phone && (
          <div style={{ fontFamily: "monospace", fontSize: 12, color: "#4a9eff", marginTop: 8 }}>📞 {lead.phone}</div>
        )}
        <div style={{ fontFamily: "monospace", fontSize: 11, color: "#C4A264", marginTop: 6 }}>
          👤 {lead.assigned_agent_name || "Non assigné"}
        </div>

        {/* Add note */}
        <div style={{ marginTop: 18 }}>
          <div style={{ fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 2, marginBottom: 6 }}>AJOUTER UNE NOTE</div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Ex: appelé, rappelle lundi..."
              style={{ flex: 1, background: "#F5F6F8", border: "1px solid #D7DAE1", borderRadius: 6, color: "#121830", padding: "9px 12px", fontSize: 13 }}
            />
            <button
              onClick={submitNote}
              disabled={savingNote || !note.trim()}
              style={{ background: "#121830", color: "#fff", border: "none", borderRadius: 6, padding: "9px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: note.trim() ? "pointer" : "default", opacity: note.trim() ? 1 : 0.5 }}
            >
              ✓
            </button>
          </div>
        </div>

        {/* Existing free-text notes */}
        {lead.crm_notes && (
          <div style={{ marginTop: 16, background: "#F5F6F8", border: "1px solid #E2E4E9", borderRadius: 6, padding: 12, whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 11, color: "#6B7280" }}>
            {lead.crm_notes.trim()}
          </div>
        )}

        {/* Timeline */}
        <div style={{ marginTop: 22 }}>
          <div style={{ fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 2, marginBottom: 10 }}>HISTORIQUE DE CONTACT</div>

          {loading ? (
            <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Chargement...</div>
          ) : activity.length === 0 ? (
            <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Aucune activité enregistrée pour ce lead.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {activity.map(item => (
                <div key={item.id} style={{ borderLeft: "2px solid #C4A264", paddingLeft: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#121830" }}>{actionLabel(item.action)}</div>
                  <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", marginTop: 2 }}>
                    {item.agent_name} · {item.timestamp ? new Date(item.timestamp).toLocaleString() : ""}
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
    </div>
  );
}
