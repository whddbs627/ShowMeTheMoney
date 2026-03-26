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
  { name: "안정형", desc: "소액·저위험", config: { k: 0.3, use_ma: true, use_rsi: true, rsi_lower: 35, loss_pct: 0.02, max_investment_krw: 50000, min_investment_krw: 5000 } },
  { name: "균형형", desc: "추천 기본값", config: { k: 0.5, use_ma: true, use_rsi: true, rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000, min_investment_krw: 5000 } },
  { name: "공격형", desc: "고수익·고위험", config: { k: 0.7, use_ma: false, use_rsi: false, rsi_lower: 20, loss_pct: 0.05, max_investment_krw: 200000, min_investment_krw: 10000 } },
];

interface Props {
  status: BotStatus | null;
  onAction: () => void;
}

export default function StatusCard({ status, onAction }: Props) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState({ k: 0.5, use_ma: true, use_rsi: true, rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000, min_investment_krw: 5000 });
  const [showStrategy, setShowStrategy] = useState(false);
  const [strategyMsg, setStrategyMsg] = useState("");

  useEffect(() => {
    getMe().then((data) => setStrategy({ ...data.strategy, min_investment_krw: data.strategy.min_investment_krw || 5000 })).catch(() => {});
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

  const handleSaveStrategy = async () => {
    await saveStrategy(strategy);
    setStrategyMsg("전략 저장됨");
    setTimeout(() => setStrategyMsg(""), 2000);
  };

  const currentPreset = PRESETS.find((p) =>
    p.config.k === strategy.k && p.config.use_ma === strategy.use_ma && p.config.use_rsi === strategy.use_rsi
  );

  return (
    <div className="card">
      <h3>자동매매 봇</h3>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: status.running ? "#22c55e" : "#ef4444", display: "inline-block" }} />
        <span style={{ fontWeight: 600, fontSize: 15 }}>{status.running ? "실행 중" : "정지"}</span>
      </div>
      <p style={{ color: "#666", fontSize: 11, marginBottom: 12 }}>변동성 돌파 전략으로 자동 매수/매도합니다</p>

      <div className="info-row"><span>감시 코인</span><span>{status.coins.length}개</span></div>
      <div className="info-row"><span>보유 중</span><span style={{ color: holdingCount > 0 ? "#22c55e" : undefined }}>{holdingCount}개</span></div>
      <div className="info-row"><span>가동 시간</span><span>{formatUptime(status.uptime_seconds)}</span></div>

      <div className="info-row" style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #333", cursor: "pointer" }} onClick={() => setShowStrategy(!showStrategy)}>
        <span>매매 전략</span>
        <span style={{ color: "#3b82f6", fontSize: 12 }}>
          {currentPreset?.name || "커스텀"} (K={strategy.k}) {showStrategy ? "▲" : "▼"}
        </span>
      </div>

      {showStrategy && (
        <div style={{ marginTop: 8, padding: 10, background: "#16162a", borderRadius: 8 }}>
          <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
            {PRESETS.map((p) => (
              <button key={p.name} onClick={() => applyPreset(p)}
                style={{
                  flex: 1, padding: "8px 4px", fontSize: 11, borderRadius: 6, border: `1px solid ${currentPreset?.name === p.name ? "#3b82f6" : "#2a2a4a"}`,
                  background: currentPreset?.name === p.name ? "#3b82f622" : "transparent",
                  color: currentPreset?.name === p.name ? "#3b82f6" : "#888", cursor: "pointer", textAlign: "center",
                }}>
                <div style={{ fontWeight: 600 }}>{p.name}</div>
                <div style={{ fontSize: 10, marginTop: 2 }}>{p.desc}</div>
              </button>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 12px", fontSize: 12 }}>
            <div className="setting-row" style={{ padding: "2px 0" }}>
              <span>K값</span>
              <input type="number" step="0.1" min="0.1" max="1.0" value={strategy.k}
                onChange={(e) => setStrategy({ ...strategy, k: +e.target.value })}
                style={{ width: 50, padding: "2px 4px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0", textAlign: "right" }} />
            </div>
            <div className="setting-row" style={{ padding: "2px 0" }}>
              <span>손절</span>
              <input type="number" step="0.01" min="0.01" max="0.2" value={strategy.loss_pct}
                onChange={(e) => setStrategy({ ...strategy, loss_pct: +e.target.value })}
                style={{ width: 50, padding: "2px 4px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0", textAlign: "right" }} />
            </div>
            <div className="setting-row" style={{ padding: "2px 0" }}>
              <span>최소 투자금</span>
              <input type="number" step="5000" min="5000" value={strategy.min_investment_krw}
                onChange={(e) => setStrategy({ ...strategy, min_investment_krw: +e.target.value })}
                style={{ width: 70, padding: "2px 4px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0", textAlign: "right" }} />
            </div>
            <div className="setting-row" style={{ padding: "2px 0" }}>
              <span>최대 투자금</span>
              <input type="number" step="10000" min="5000" value={strategy.max_investment_krw}
                onChange={(e) => setStrategy({ ...strategy, max_investment_krw: +e.target.value })}
                style={{ width: 70, padding: "2px 4px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0", textAlign: "right" }} />
            </div>
            <div className="setting-row" style={{ padding: "2px 0" }}>
              <span>MA필터</span>
              <input type="checkbox" checked={strategy.use_ma} onChange={(e) => setStrategy({ ...strategy, use_ma: e.target.checked })} />
            </div>
            <div className="setting-row" style={{ padding: "2px 0" }}>
              <span>RSI필터</span>
              <input type="checkbox" checked={strategy.use_rsi} onChange={(e) => setStrategy({ ...strategy, use_rsi: e.target.checked })} />
            </div>
          </div>

          <button onClick={handleSaveStrategy}
            style={{ width: "100%", marginTop: 8, padding: "6px", fontSize: 12, borderRadius: 4, border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer" }}>
            전략 저장
          </button>
          {strategyMsg && <div style={{ color: "#22c55e", fontSize: 11, marginTop: 4, textAlign: "center" }}>{strategyMsg}</div>}
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
