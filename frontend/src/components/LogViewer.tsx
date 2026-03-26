import { useState, useEffect, useRef } from "react";

const BASE = "/api";

export default function LogViewer() {
  const [userLogs, setUserLogs] = useState<string[]>([]);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);
  const [tab, setTab] = useState<"system" | "user">("system");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${BASE}/logs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUserLogs(data.user_logs || []);
        setSystemLogs(data.system_logs || []);
      }
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchLogs();
    if (!autoRefresh) return;
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [userLogs, systemLogs]);

  const logs = tab === "system" ? systemLogs : userLogs;

  return (
    <div className="card">
      <h3>
        Logs
        <button
          onClick={() => setAutoRefresh(!autoRefresh)}
          style={{
            marginLeft: 12, padding: "2px 10px", fontSize: 11,
            borderRadius: 4, border: "1px solid #333",
            background: autoRefresh ? "#22c55e22" : "transparent",
            color: autoRefresh ? "#22c55e" : "#888",
            cursor: "pointer",
          }}
        >
          {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
        </button>
        <button
          onClick={fetchLogs}
          style={{
            marginLeft: 8, padding: "2px 10px", fontSize: 11,
            borderRadius: 4, border: "1px solid #333",
            background: "transparent", color: "#888", cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button
          onClick={() => setTab("system")}
          style={{
            padding: "4px 12px", fontSize: 12, borderRadius: 4, border: "none", cursor: "pointer",
            background: tab === "system" ? "#3b82f6" : "#16162a", color: "#fff",
          }}
        >
          System
        </button>
        <button
          onClick={() => setTab("user")}
          style={{
            padding: "4px 12px", fontSize: 12, borderRadius: 4, border: "none", cursor: "pointer",
            background: tab === "user" ? "#3b82f6" : "#16162a", color: "#fff",
          }}
        >
          Bot Activity
        </button>
      </div>
      <div
        style={{
          background: "#0a0a1a", borderRadius: 8, padding: 12,
          maxHeight: 400, overflowY: "auto", fontFamily: "monospace", fontSize: 12,
          lineHeight: 1.6, color: "#a0a0a0",
        }}
      >
        {logs.length === 0 ? (
          <p style={{ color: "#555" }}>No logs yet.</p>
        ) : (
          logs.map((line, i) => (
            <div
              key={i}
              style={{
                color: line.includes("ERROR") || line.includes("error")
                  ? "#ef4444"
                  : line.includes("WARNING") || line.includes("warning")
                  ? "#eab308"
                  : line.includes("BUY") || line.includes("SELL")
                  ? "#22c55e"
                  : "#a0a0a0",
              }}
            >
              {line}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
