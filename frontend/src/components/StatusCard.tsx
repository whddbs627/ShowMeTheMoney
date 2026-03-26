import { useState } from "react";
import { startBot, stopBot } from "../api";
import type { BotStatus } from "../types";

function formatUptime(seconds: number | null): string {
  if (!seconds) return "-";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h}h ${m}m ${s}s`;
}

interface Props {
  status: BotStatus | null;
  onAction: () => void;
}

export default function StatusCard({ status, onAction }: Props) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!status) return <div className="card">Loading...</div>;

  const holdingCount = status.coins.filter((c) => c.state === "holding").length;

  const handleStart = async () => {
    setError("");
    setLoading(true);
    try {
      await startBot();
      onAction();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start failed");
    }
    setLoading(false);
  };

  const handleStop = async () => {
    setError("");
    setLoading(true);
    try {
      await stopBot();
      onAction();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    }
    setLoading(false);
  };

  return (
    <div className="card">
      <h3>Bot Status</h3>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span
          style={{
            width: 12, height: 12, borderRadius: "50%",
            backgroundColor: status.running ? "#22c55e" : "#ef4444",
            display: "inline-block",
          }}
        />
        <span style={{ fontWeight: 600 }}>{status.running ? "RUNNING" : "STOPPED"}</span>
      </div>
      <div className="info-row"><span>Coins</span><span>{status.coins.length}</span></div>
      <div className="info-row"><span>Holding</span><span style={{ color: holdingCount > 0 ? "#22c55e" : undefined }}>{holdingCount}</span></div>
      <div className="info-row"><span>Uptime</span><span>{formatUptime(status.uptime_seconds)}</span></div>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <button className="btn btn-start" disabled={status.running || loading} onClick={handleStart}>
          {loading && !status.running ? "Starting..." : "Start"}
        </button>
        <button className="btn btn-stop" disabled={!status.running || loading} onClick={handleStop}>
          {loading && status.running ? "Stopping..." : "Stop"}
        </button>
      </div>
      {error && <p style={{ color: "#ef4444", fontSize: 12, marginTop: 8 }}>{error}</p>}
    </div>
  );
}
