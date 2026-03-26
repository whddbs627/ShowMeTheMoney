import { useState, useEffect } from "react";
import { getLeaderboard } from "../api";

interface Entry {
  username: string; total_trades: number; total_pnl_krw: number; avg_pnl_pct: number;
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
      <h3>수익률 순위</h3>
      {data.length === 0 ? (
        <p style={{ color: "#888", fontSize: 13 }}>아직 매매 데이터가 없습니다.</p>
      ) : (
        <table>
          <thead><tr><th>#</th><th>유저</th><th>매매 횟수</th><th>총 수익</th><th>평균 수익률</th></tr></thead>
          <tbody>
            {data.map((entry, i) => (
              <tr key={entry.username}>
                <td style={{ color: i < 3 ? "#eab308" : "#888", fontWeight: i < 3 ? 700 : 400 }}>{i + 1}</td>
                <td style={{ fontWeight: 600 }}>{entry.username}</td>
                <td>{entry.total_trades}회</td>
                <td style={{ color: entry.total_pnl_krw >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                  {entry.total_pnl_krw >= 0 ? "+" : ""}{entry.total_pnl_krw?.toLocaleString() || 0}원
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
