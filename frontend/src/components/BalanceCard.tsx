import type { BalanceInfo, PnlPoint } from "../types";

interface Props {
  balance: BalanceInfo | null;
  pnl: PnlPoint[];
}

export default function BalanceCard({ balance, pnl }: Props) {
  if (!balance) return <div className="card">Loading...</div>;

  const holdingCoins = balance.coins.filter((c) => c.value_krw > 0);
  const totalPnl = pnl.length > 0 ? pnl[pnl.length - 1].cumulative_pnl_krw : 0;

  return (
    <div className="card">
      <h3>자산 / 수익</h3>
      <div className="info-row">
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
