import type { CoinStatus } from "../types";
import { removeFromWatchlist } from "../api";

interface Props {
  coins: CoinStatus[];
  watchlist: string[];
  onRemove: () => void;
  lossPct: number;
}

export default function PriceDisplay({ coins, watchlist, onRemove, lossPct }: Props) {
  const handleRemove = async (ticker: string) => {
    await removeFromWatchlist(ticker);
    onRemove();
  };

  const allTickers = [...new Set([...watchlist, ...coins.map((c) => c.ticker)])];

  if (allTickers.length === 0) {
    return (
      <div className="card">
        <h3>내 코인</h3>
        <p style={{ color: "#888", fontSize: 13 }}>코인을 검색하고 추가하세요.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>내 코인 ({allTickers.length}개)</h3>
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
              <th>매수가</th>
              <th>수익률</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {allTickers.map((ticker) => {
              const c = coins.find((x) => x.ticker === ticker);
              const isHolding = c?.state === "holding";
              const stopLoss = c?.buy_price ? c.buy_price * (1 - lossPct) : null;
              const pnl = isHolding && c?.current_price && c?.buy_price
                ? ((c.current_price - c.buy_price) / c.buy_price) * 100 : null;

              return (
                <tr key={ticker}>
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
                  <td>{c?.buy_price ? c.buy_price.toLocaleString() : "-"}</td>
                  <td style={{ color: pnl !== null ? (pnl >= 0 ? "#22c55e" : "#ef4444") : undefined, fontWeight: pnl !== null ? 600 : 400 }}>
                    {pnl !== null ? `${pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}%` : "-"}
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
