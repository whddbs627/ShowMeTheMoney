import type { TradeRecord } from "../types";

export default function TradeTable({ trades }: { trades: TradeRecord[] }) {
  if (trades.length === 0) {
    return (
      <div className="card">
        <h3>Trade History</h3>
        <p style={{ color: "#888" }}>No trades yet.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>Trade History</h3>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Side</th>
              <th>Ticker</th>
              <th>Price</th>
              <th>Amount</th>
              <th>Reason</th>
              <th>P&L</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => (
              <tr key={t.id}>
                <td>{new Date(t.timestamp).toLocaleString("ko-KR")}</td>
                <td style={{ color: t.side === "BUY" ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                  {t.side}
                </td>
                <td>{t.ticker}</td>
                <td>{t.price.toLocaleString()}</td>
                <td>{t.amount_krw.toLocaleString()} KRW</td>
                <td>{t.reason || "-"}</td>
                <td style={{ color: t.pnl_pct && t.pnl_pct >= 0 ? "#22c55e" : "#ef4444" }}>
                  {t.pnl_pct != null ? `${t.pnl_pct > 0 ? "+" : ""}${t.pnl_pct.toFixed(2)}%` : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
