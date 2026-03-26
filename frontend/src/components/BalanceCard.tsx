import { useState, useEffect } from "react";
import type { BalanceInfo, PnlPoint } from "../types";
import { getMe, toggleDemo } from "../api";

interface Props {
  balance: BalanceInfo | null;
  pnl: PnlPoint[];
}

export default function BalanceCard({ balance, pnl }: Props) {
  const [isDemo, setIsDemo] = useState(false);
  const [demoAmount, setDemoAmount] = useState("10000000");
  const [showDemoSetup, setShowDemoSetup] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getMe().then((data) => {
      setIsDemo(data.is_demo);
      setDemoAmount(String(data.demo_balance));
    });
  }, []);

  const handleToggle = async () => {
    const newDemo = !isDemo;
    const amount = parseFloat(demoAmount) || 10000000;
    try {
      await toggleDemo(newDemo, amount);
      setIsDemo(newDemo);
      setMsg(newDemo ? "가상계좌 모드 활성화" : "실제계좌 모드 전환");
      setShowDemoSetup(false);
      setTimeout(() => setMsg(""), 2000);
      window.location.reload();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "전환 실패");
    }
  };

  if (!balance) return <div className="card">Loading...</div>;

  const holdingCoins = balance.coins.filter((c) => c.value_krw > 0);
  const totalPnl = pnl.length > 0 ? pnl[pnl.length - 1].cumulative_pnl_krw : 0;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>자산 / 수익</h3>
        <button onClick={() => setShowDemoSetup(!showDemoSetup)}
          style={{
            padding: "3px 8px", fontSize: 10, borderRadius: 4, border: "none", cursor: "pointer",
            background: isDemo ? "#eab30822" : "#16162a",
            color: isDemo ? "#eab308" : "#888",
          }}>
          {isDemo ? "가상계좌" : "실제계좌"}
        </button>
      </div>

      {showDemoSetup && (
        <div style={{ marginTop: 8, padding: 8, background: "#16162a", borderRadius: 6 }}>
          <div style={{ marginBottom: 6 }}>
            <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
              {[1000000, 10000000, 100000000, 1000000000].map((v) => (
                <button key={v} onClick={() => setDemoAmount(String(v))}
                  style={{
                    flex: 1, padding: "4px", fontSize: 10, borderRadius: 4, border: "none", cursor: "pointer",
                    background: demoAmount === String(v) ? "#3b82f622" : "#0f0f23",
                    color: demoAmount === String(v) ? "#3b82f6" : "#888",
                  }}>
                  {v >= 100000000 ? `${v / 100000000}억` : `${v / 10000}만`}
                </button>
              ))}
            </div>
            <input type="text" inputMode="numeric" placeholder="가상 잔고 (원)" value={Number(demoAmount).toLocaleString()}
              onChange={(e) => setDemoAmount(e.target.value.replace(/[^0-9]/g, ""))}
              style={{ width: "100%", padding: "6px 8px", fontSize: 12, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0", boxSizing: "border-box", textAlign: "right" }} />
            <p style={{ color: "#666", fontSize: 10, margin: "4px 0 0" }}>{isDemo ? "보유 원화를 변경합니다" : "가상 보유 코인은 초기화됩니다"}</p>
          </div>
          <button onClick={handleToggle}
            style={{ width: "100%", padding: "6px", fontSize: 11, borderRadius: 4, border: "none", cursor: "pointer", background: isDemo ? "#3b82f6" : "#eab308", color: isDemo ? "#fff" : "#000" }}>
            {isDemo ? "실제계좌로 전환" : "가상계좌로 전환"}
          </button>
        </div>
      )}

      {msg && <div style={{ color: "#22c55e", fontSize: 11, marginTop: 4 }}>{msg}</div>}

      <div className="info-row" style={{ marginTop: 8 }}>
        <span>보유 원화</span>
        <span>{balance.krw_balance != null ? `${balance.krw_balance.toLocaleString()}원` : "-"}</span>
      </div>
      {holdingCoins.map((c) => (
        <div className="info-row" key={c.ticker}>
          <span>{c.ticker.replace("KRW-", "")}</span>
          <span>{c.value_krw.toLocaleString()}원</span>
        </div>
      ))}
      <div className="info-row" style={{ fontWeight: 700, borderTop: "1px solid #333", paddingTop: 8, marginTop: 4 }}>
        <span>총 자산</span>
        <span>{balance.total_krw != null ? `${balance.total_krw.toLocaleString()}원` : "-"}</span>
      </div>
      <div className="info-row" style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #333" }}>
        <span>누적 수익</span>
        <span style={{ color: totalPnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 700 }}>
          {totalPnl >= 0 ? "+" : ""}{totalPnl.toLocaleString()}원
        </span>
      </div>
      <div className="info-row">
        <span>매도 횟수</span>
        <span>{pnl.length}회</span>
      </div>
    </div>
  );
}
