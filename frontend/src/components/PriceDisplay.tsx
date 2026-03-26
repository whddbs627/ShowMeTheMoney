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

  // Show watchlist tickers even when bot is stopped (no coin data)
  const allTickers = [...new Set([...watchlist, ...coins.map((c) => c.ticker)])];

  if (allTickers.length === 0) {
    return (
      <div className="card">
        <h3>My Coins</h3>
        <p style={{ color: "#888", fontSize: 13 }}>Search and add coins to start trading.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>My Coins ({allTickers.length})</h3>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Coin</th>
              <th>State</th>
              <th>Price</th>
              <th>Target</th>
              <th>Stop Loss</th>
              <th>RSI</th>
              <th>MA</th>
              <th>Buy</th>
              <th>P&L</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {allTickers.map((ticker) => {
              const c = coins.find((x) => x.ticker === ticker);
              const isHolding = c?.state === "holding";
              const stopLoss = c?.buy_price ? c.buy_price * (1 - lossPct) : null;
              const pnl = isHolding && c?.current_price && c?.buy_price
                ? ((c.current_price - c.buy_price) / c.buy_price) * 100
                : null;

              return (
                <tr key={ticker}>
                  <td style={{ fontWeight: 600 }}>{ticker.replace("KRW-", "")}</td>
                  <td>
                    <span style={{ color: isHolding ? "#22c55e" : "#555", fontWeight: 600, fontSize: 12 }}>
                      {isHolding ? "HOLDING" : c ? "WAITING" : "-"}
                    </span>
                  </td>
                  <td>{c?.current_price ? c.current_price.toLocaleString() : "-"}</td>
                  <td style={{ color: "#3b82f6" }}>
                    {c?.target_price ? c.target_price.toLocaleString() : "-"}
                  </td>
                  <td style={{ color: "#ef4444" }}>
                    {stopLoss ? stopLoss.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "-"}
                  </td>
                  <td style={{ color: c?.rsi && c.rsi < 30 ? "#ef4444" : undefined }}>
                    {c?.rsi ? c.rsi.toFixed(1) : "-"}
                  </td>
                  <td style={{ color: c?.ma_bullish ? "#22c55e" : c?.ma_bullish === false ? "#ef4444" : undefined }}>
                    {c?.ma_bullish === null || c?.ma_bullish === undefined ? "-" : c.ma_bullish ? "UP" : "DOWN"}
                  </td>
                  <td>{c?.buy_price ? c.buy_price.toLocaleString() : "-"}</td>
                  <td style={{
                    color: pnl !== null ? (pnl >= 0 ? "#22c55e" : "#ef4444") : undefined,
                    fontWeight: pnl !== null ? 600 : 400,
                  }}>
                    {pnl !== null ? `${pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}%` : "-"}
                  </td>
                  <td>
                    <button
                      onClick={() => handleRemove(ticker)}
                      disabled={isHolding}
                      style={{
                        background: "none", border: "none", color: isHolding ? "#333" : "#ef4444",
                        cursor: isHolding ? "default" : "pointer", fontSize: 14,
                      }}
                      title={isHolding ? "Can't remove while holding" : "Remove from watchlist"}
                    >
                      x
                    </button>
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
