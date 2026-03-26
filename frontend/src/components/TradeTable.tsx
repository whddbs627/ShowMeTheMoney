import type { TradeRecord } from "../types";

export default function TradeTable({ trades }: { trades: TradeRecord[] }) {
  if (trades.length === 0) {
    return (
      <div className="card">
        <h3>매매 내역</h3>
        <p style={{ color: "#888", fontSize: 13 }}>아직 매매 내역이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>매매 내역</h3>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>시간</th>
              <th>구분</th>
              <th>코인</th>
              <th>가격</th>
              <th>금액</th>
              <th>사유</th>
              <th>수익률</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => (
              <tr key={t.id}>
                <td>{new Date(t.timestamp).toLocaleString("ko-KR")}</td>
                <td style={{ color: t.side === "BUY" ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                  {t.side === "BUY" ? "매수" : "매도"}
                </td>
                <td>{t.ticker}</td>
                <td>{t.price.toLocaleString()}</td>
                <td>{t.amount_krw.toLocaleString()}원</td>
                <td>{t.reason === "NEXT_DAY" ? "익일매도" : t.reason === "STOP_LOSS" ? "손절" : "-"}</td>
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
