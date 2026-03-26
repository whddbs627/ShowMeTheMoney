import type { CoinStatus } from "../types";

export default function PriceDisplay({ coins }: { coins: CoinStatus[] }) {
  if (coins.length === 0) return <div className="card"><h3>Coin Status</h3><p style={{color:"#888",fontSize:13}}>Add coins to watchlist and start the bot.</p></div>;

  return (
    <div className="card" style={{ gridColumn: "1 / -1" }}>
      <h3>Coin Status</h3>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Coin</th>
              <th>State</th>
              <th>Price</th>
              <th>Target</th>
              <th>RSI</th>
              <th>MA</th>
              <th>Buy Price</th>
            </tr>
          </thead>
          <tbody>
            {coins.map((c) => (
              <tr key={c.ticker}>
                <td style={{ fontWeight: 600 }}>{c.ticker.replace("KRW-", "")}</td>
                <td>
                  <span
                    style={{
                      color: c.state === "holding" ? "#22c55e" : "#888",
                      fontWeight: 600,
                    }}
                  >
                    {c.state === "holding" ? "HOLDING" : "WAITING"}
                  </span>
                </td>
                <td>{c.current_price ? c.current_price.toLocaleString() : "-"}</td>
                <td>{c.target_price ? c.target_price.toLocaleString() : "-"}</td>
                <td style={{ color: c.rsi && c.rsi < 30 ? "#ef4444" : undefined }}>
                  {c.rsi ? c.rsi.toFixed(1) : "-"}
                </td>
                <td style={{ color: c.ma_bullish ? "#22c55e" : "#ef4444" }}>
                  {c.ma_bullish === null ? "-" : c.ma_bullish ? "UP" : "DOWN"}
                </td>
                <td>{c.buy_price ? c.buy_price.toLocaleString() : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
