import type { BotStatus } from "../types";

function formatUptime(seconds: number | null): string {
  if (!seconds) return "-";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h}h ${m}m ${s}s`;
}

export default function StatusCard({ status }: { status: BotStatus | null }) {
  if (!status) return <div className="card">Loading...</div>;

  const holdingCount = status.coins.filter((c) => c.state === "holding").length;

  return (
    <div className="card">
      <h3>Bot Status</h3>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: "50%",
            backgroundColor: status.running ? "#22c55e" : "#ef4444",
            display: "inline-block",
          }}
        />
        <span style={{ fontWeight: 600 }}>{status.running ? "RUNNING" : "STOPPED"}</span>
      </div>
      <div className="info-row">
        <span>Coins</span>
        <span>{status.coins.length}</span>
      </div>
      <div className="info-row">
        <span>Holding</span>
        <span style={{ color: holdingCount > 0 ? "#22c55e" : undefined }}>{holdingCount}</span>
      </div>
      <div className="info-row">
        <span>Uptime</span>
        <span>{formatUptime(status.uptime_seconds)}</span>
      </div>
    </div>
  );
}
