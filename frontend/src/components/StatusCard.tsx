import { useState, useEffect } from "react";
import { startBot, stopBot, getMe, saveStrategy } from "../api";
import type { BotStatus } from "../types";

function formatUptime(seconds: number | null): string {
  if (!seconds) return "-";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}시간 ${m}분`;
}

const PRESETS = [
  { name: "안정형", config: { k: 0.3, use_ma: true, use_rsi: true, rsi_lower: 35, loss_pct: 0.02, max_investment_krw: 50000 } },
  { name: "균형형", config: { k: 0.5, use_ma: true, use_rsi: true, rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000 } },
  { name: "공격형", config: { k: 0.7, use_ma: false, use_rsi: false, rsi_lower: 20, loss_pct: 0.05, max_investment_krw: 200000 } },
];

interface Props {
  status: BotStatus | null;
  onAction: () => void;
}

export default function StatusCard({ status, onAction }: Props) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState({ k: 0.5, use_ma: true, use_rsi: true, rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000 });
  const [showStrategy, setShowStrategy] = useState(false);
  const [strategyMsg, setStrategyMsg] = useState("");

  useEffect(() => {
    getMe().then((data) => setStrategy(data.strategy)).catch(() => {});
  }, []);

  if (!status) return <div className="card">Loading...</div>;

  const holdingCount = status.coins.filter((c) => c.state === "holding").length;

  const handleStart = async () => {
    setError(""); setLoading(true);
    try { await startBot(); onAction(); }
    catch (e) { setError(e instanceof Error ? e.message : "시작 실패"); }
    setLoading(false);
  };

  const handleStop = async () => {
    setError(""); setLoading(true);
    try { await stopBot(); onAction(); }
    catch (e) { setError(e instanceof Error ? e.message : "중지 실패"); }
    setLoading(false);
  };

  const applyPreset = async (preset: typeof PRESETS[0]) => {
    setStrategy(preset.config);
    await saveStrategy(preset.config);
    setStrategyMsg(`${preset.name} 전략 적용됨`);
    setTimeout(() => setStrategyMsg(""), 2000);
  };

  const currentPreset = PRESETS.find((p) =>
    p.config.k === strategy.k && p.config.use_ma === strategy.use_ma && p.config.use_rsi === strategy.use_rsi
  );

  return (
    <div className="card">
      <h3>봇 상태</h3>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: status.running ? "#22c55e" : "#ef4444", display: "inline-block" }} />
        <span style={{ fontWeight: 600 }}>{status.running ? "실행 중" : "정지"}</span>
      </div>
      <div className="info-row"><span>감시 코인</span><span>{status.coins.length}개</span></div>
      <div className="info-row"><span>보유 중</span><span style={{ color: holdingCount > 0 ? "#22c55e" : undefined }}>{holdingCount}개</span></div>
      <div className="info-row"><span>가동 시간</span><span>{formatUptime(status.uptime_seconds)}</span></div>

      <div className="info-row" style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #333" }}>
        <span>매매 전략</span>
        <span style={{ color: "#3b82f6", cursor: "pointer", fontSize: 12 }} onClick={() => setShowStrategy(!showStrategy)}>
          {currentPreset?.name || "커스텀"} (K={strategy.k}) {showStrategy ? "▲" : "▼"}
        </span>
      </div>

      {showStrategy && (
        <div style={{ marginTop: 8, padding: 8, background: "#16162a", borderRadius: 8 }}>
          <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
            {PRESETS.map((p) => (
              <button key={p.name} onClick={() => applyPreset(p)}
                style={{
                  flex: 1, padding: "6px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a",
                  background: currentPreset?.name === p.name ? "#3b82f622" : "transparent",
                  color: currentPreset?.name === p.name ? "#3b82f6" : "#888", cursor: "pointer",
                }}>
                {p.name}
              </button>
            ))}
          </div>
          <div style={{ fontSize: 11, color: "#888", lineHeight: 1.8 }}>
            K값: {strategy.k} | MA필터: {strategy.use_ma ? "ON" : "OFF"} | RSI필터: {strategy.use_rsi ? "ON" : "OFF"}
            <br/>손절: {(strategy.loss_pct * 100).toFixed(0)}% | 코인당: {strategy.max_investment_krw.toLocaleString()}원
          </div>
          {strategyMsg && <div style={{ color: "#22c55e", fontSize: 11, marginTop: 4 }}>{strategyMsg}</div>}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
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
