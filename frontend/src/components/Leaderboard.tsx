import { useState, useEffect } from "react";
import { getLeaderboard } from "../api";

interface Entry {
  username: string;
  total_trades: number;
  total_pnl_krw: number;
  avg_pnl_pct: number;
}

export default function Leaderboard() {
  const [data, setData] = useState<Entry[]>([]);

  useEffect(() => {
    getLeaderboard().then(setData);
    const interval = setInterval(() => getLeaderboard().then(setData), 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <h3>Leaderboard</h3>
      {data.length === 0 ? (
        <p style={{ color: "#888", fontSize: 13 }}>No trading data yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>User</th>
              <th>Trades</th>
              <th>Total P&L</th>
              <th>Avg P&L</th>
            </tr>
          </thead>
          <tbody>
            {data.map((entry, i) => (
              <tr key={entry.username}>
                <td style={{ color: i < 3 ? "#eab308" : "#888", fontWeight: i < 3 ? 700 : 400 }}>
                  {i + 1}
                </td>
                <td style={{ fontWeight: 600 }}>{entry.username}</td>
                <td>{entry.total_trades}</td>
                <td style={{ color: entry.total_pnl_krw >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                  {entry.total_pnl_krw >= 0 ? "+" : ""}{entry.total_pnl_krw?.toLocaleString() || 0} KRW
                </td>
                <td style={{ color: (entry.avg_pnl_pct || 0) >= 0 ? "#22c55e" : "#ef4444" }}>
                  {entry.avg_pnl_pct ? `${entry.avg_pnl_pct > 0 ? "+" : ""}${entry.avg_pnl_pct.toFixed(2)}%` : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
