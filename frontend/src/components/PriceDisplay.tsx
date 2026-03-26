import { useState } from "react";
import type { CoinStatus } from "../types";
import { removeFromWatchlist, manualBuy, manualSell } from "../api";

type SortKey = "default" | "name" | "price" | "change" | "rsi";

interface Props {
  coins: CoinStatus[];
  watchlist: string[];
  onRemove: () => void;
  onTrade: () => void;
  lossPct: number;
}

export default function PriceDisplay({ coins, watchlist, onRemove, onTrade, lossPct }: Props) {
  const [buyAmounts, setBuyAmounts] = useState<Record<string, string>>({});
  const [sellPrices, setSellPrices] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [msg, setMsg] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("default");

  const allTickers = [...new Set([...watchlist, ...coins.map((c) => c.ticker)])];

  // 코인 데이터 매핑
  const rows = allTickers.map((ticker) => {
    const c = coins.find((x) => x.ticker === ticker);
    const isHolding = c?.state === "holding";
    const stopLoss = c?.buy_price ? c.buy_price * (1 - lossPct) : null;
    const pnl = isHolding && c?.current_price && c?.buy_price
      ? ((c.current_price - c.buy_price) / c.buy_price) * 100 : null;
    return { ticker, c, isHolding: !!isHolding, stopLoss, pnl, price: c?.current_price || 0, rsi: c?.rsi || 0 };
  });

  // 정렬: 보유 코인 항상 상단 + 선택한 정렬 기준
  rows.sort((a, b) => {
    // 보유 코인 우선
    if (a.isHolding !== b.isHolding) return a.isHolding ? -1 : 1;
    // 세부 정렬
    switch (sortKey) {
      case "name": return a.ticker.localeCompare(b.ticker);
      case "price": return b.price - a.price;
      case "change": return (b.pnl || 0) - (a.pnl || 0);
      case "rsi": return a.rsi - b.rsi;
      default: return 0;
    }
  });

  const handleRemove = async (ticker: string) => { await removeFromWatchlist(ticker); onRemove(); };

  const handleBuy = async (ticker: string) => {
    const amount = parseInt(buyAmounts[ticker] || "0");
    if (amount < 5000) { showMsg("최소 5,000원 이상 입력하세요"); return; }
    setLoading((p) => ({ ...p, [ticker]: true }));
    try {
      showMsg((await manualBuy(ticker, amount)).message);
      setBuyAmounts((p) => ({ ...p, [ticker]: "" }));
      onTrade();
    } catch (e) { showMsg(e instanceof Error ? e.message : "매수 실패"); }
    setLoading((p) => ({ ...p, [ticker]: false }));
  };

  const handleSell = async (ticker: string) => {
    const limitPrice = sellPrices[ticker] ? parseFloat(sellPrices[ticker]) : undefined;
    setLoading((p) => ({ ...p, [ticker]: true }));
    try {
      showMsg((await manualSell(ticker, limitPrice)).message);
      setSellPrices((p) => ({ ...p, [ticker]: "" }));
      onTrade();
    } catch (e) { showMsg(e instanceof Error ? e.message : "매도 실패"); }
    setLoading((p) => ({ ...p, [ticker]: false }));
  };

  const showMsg = (text: string) => { setMsg(text); setTimeout(() => setMsg(""), 3000); };

  const holdingCount = rows.filter((r) => r.isHolding).length;

  if (rows.length === 0) {
    return (
      <div className="card">
        <h3>내 코인</h3>
        <p style={{ color: "#888", fontSize: 13 }}>코인을 검색하고 추가하세요.</p>
      </div>
    );
  }

  const SORT_OPTIONS: { key: SortKey; label: string }[] = [
    { key: "default", label: "기본" },
    { key: "name", label: "이름" },
    { key: "price", label: "가격" },
    { key: "change", label: "수익률" },
    { key: "rsi", label: "RSI" },
  ];

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>내 코인 ({rows.length}개{holdingCount > 0 ? ` · 보유 ${holdingCount}` : ""})</h3>
        <div style={{ display: "flex", gap: 4 }}>
          {SORT_OPTIONS.map((opt) => (
            <button key={opt.key} onClick={() => setSortKey(opt.key)}
              style={{
                padding: "3px 8px", fontSize: 10, borderRadius: 4, border: "none", cursor: "pointer",
                background: sortKey === opt.key ? "#3b82f6" : "#16162a",
                color: sortKey === opt.key ? "#fff" : "#666",
              }}>
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {msg && (
        <div style={{ background: msg.includes("실패") ? "#ef444422" : "#22c55e22", border: `1px solid ${msg.includes("실패") ? "#ef4444" : "#22c55e"}`, borderRadius: 6, padding: "6px 12px", marginBottom: 12, fontSize: 12, color: msg.includes("실패") ? "#ef4444" : "#22c55e" }}>
          {msg}
        </div>
      )}

      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>코인</th>
              <th>상태</th>
              <th>현재가</th>
              <th>목표가</th>
              <th>손절가</th>
              <th>RSI</th>
              <th>추세</th>
              <th>수익률</th>
              <th>매매</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ ticker, c, isHolding, stopLoss, pnl }) => {
              const isLoading = loading[ticker];
              return (
                <tr key={ticker} style={{ background: isHolding ? "#22c55e08" : undefined }}>
                  <td style={{ fontWeight: 600 }}>{ticker.replace("KRW-", "")}</td>
                  <td>
                    <span style={{ color: isHolding ? "#22c55e" : "#555", fontWeight: 600, fontSize: 12 }}>
                      {isHolding ? "보유" : c ? "대기" : "-"}
                    </span>
                  </td>
                  <td>{c?.current_price ? c.current_price.toLocaleString() : "-"}</td>
                  <td style={{ color: "#3b82f6" }}>{c?.target_price ? c.target_price.toLocaleString() : "-"}</td>
                  <td style={{ color: "#ef4444" }}>{stopLoss ? stopLoss.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "-"}</td>
                  <td style={{ color: c?.rsi && c.rsi < 30 ? "#ef4444" : undefined }}>{c?.rsi ? c.rsi.toFixed(1) : "-"}</td>
                  <td style={{ color: c?.ma_bullish ? "#22c55e" : c?.ma_bullish === false ? "#ef4444" : undefined }}>
                    {c?.ma_bullish == null ? "-" : c.ma_bullish ? "상승" : "하락"}
                  </td>
                  <td style={{ color: pnl !== null ? (pnl >= 0 ? "#22c55e" : "#ef4444") : undefined, fontWeight: pnl !== null ? 600 : 400 }}>
                    {pnl !== null ? `${pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}%` : "-"}
                  </td>
                  <td>
                    {isHolding ? (
                      <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
                        <input type="number" placeholder="지정가" value={sellPrices[ticker] || ""}
                          onChange={(e) => setSellPrices((p) => ({ ...p, [ticker]: e.target.value }))}
                          style={{ width: 75, padding: "3px 6px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0" }} />
                        <button onClick={() => handleSell(ticker)} disabled={isLoading}
                          style={{ padding: "3px 8px", fontSize: 11, borderRadius: 4, border: "none", background: "#ef4444", color: "#fff", cursor: "pointer", whiteSpace: "nowrap" }}>
                          {isLoading ? "..." : sellPrices[ticker] ? "지정매도" : "시장매도"}
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
                        <input type="number" placeholder="금액(원)" value={buyAmounts[ticker] || ""}
                          onChange={(e) => setBuyAmounts((p) => ({ ...p, [ticker]: e.target.value }))}
                          style={{ width: 75, padding: "3px 6px", fontSize: 11, borderRadius: 4, border: "1px solid #2a2a4a", background: "#0f0f23", color: "#f0f0f0" }} />
                        <button onClick={() => handleBuy(ticker)} disabled={isLoading}
                          style={{ padding: "3px 8px", fontSize: 11, borderRadius: 4, border: "none", background: "#22c55e", color: "#000", cursor: "pointer", whiteSpace: "nowrap" }}>
                          {isLoading ? "..." : "매수"}
                        </button>
                      </div>
                    )}
                  </td>
                  <td>
                    <button onClick={() => handleRemove(ticker)} disabled={isHolding}
                      style={{ background: "none", border: "none", color: isHolding ? "#333" : "#ef4444", cursor: isHolding ? "default" : "pointer", fontSize: 14 }}
                      title={isHolding ? "보유 중에는 제거 불가" : "삭제"}>x</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
