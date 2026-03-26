import { useState } from "react";
import { startBot, stopBot } from "../api";
import type { BotStatus } from "../types";

function formatUptime(seconds: number | null): string {
  if (!seconds) return "-";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}시간 ${m}분`;
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
    try { await startBot(); onAction(); }
    catch (e) { setError(e instanceof Error ? e.message : "시작 실패"); }
    setLoading(false);
  };

  const handleStop = async () => {
    setError("");
    setLoading(true);
    try { await stopBot(); onAction(); }
    catch (e) { setError(e instanceof Error ? e.message : "중지 실패"); }
    setLoading(false);
  };

  return (
    <div className="card">
      <h3>봇 상태</h3>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span style={{
          width: 12, height: 12, borderRadius: "50%",
          backgroundColor: status.running ? "#22c55e" : "#ef4444",
          display: "inline-block",
        }} />
        <span style={{ fontWeight: 600 }}>{status.running ? "실행 중" : "정지"}</span>
      </div>
      <div className="info-row"><span>감시 코인</span><span>{status.coins.length}개</span></div>
      <div className="info-row"><span>보유 중</span><span style={{ color: holdingCount > 0 ? "#22c55e" : undefined }}>{holdingCount}개</span></div>
      <div className="info-row"><span>가동 시간</span><span>{formatUptime(status.uptime_seconds)}</span></div>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <button className="btn btn-start" disabled={status.running || loading} onClick={handleStart}>
          {loading && !status.running ? "시작 중..." : "시작"}
        </button>
        <button className="btn btn-stop" disabled={!status.running || loading} onClick={handleStop}>
          {loading && status.running ? "중지 중..." : "중지"}
        </button>
      </div>
      {error && <p style={{ color: "#ef4444", fontSize: 12, marginTop: 8 }}>{error}</p>}
    </div>
  );
}
