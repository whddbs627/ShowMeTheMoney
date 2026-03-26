import type { BalanceInfo } from "../types";

export default function BalanceCard({ balance }: { balance: BalanceInfo | null }) {
  if (!balance) return <div className="card">Loading...</div>;

  const holdingCoins = balance.coins.filter((c) => c.value_krw > 0);

  return (
    <div className="card">
      <h3>Balance</h3>
      <div className="info-row">
        <span>KRW</span>
        <span>{balance.krw_balance != null ? `${balance.krw_balance.toLocaleString()} KRW` : "-"}</span>
      </div>
      {holdingCoins.map((c) => (
        <div className="info-row" key={c.ticker}>
          <span>{c.ticker.replace("KRW-", "")}</span>
          <span>{c.value_krw.toLocaleString()} KRW</span>
        </div>
      ))}
      <div
        className="info-row"
        style={{ fontWeight: 700, borderTop: "1px solid #333", paddingTop: 8, marginTop: 4 }}
      >
        <span>Total</span>
        <span>{balance.total_krw != null ? `${balance.total_krw.toLocaleString()} KRW` : "-"}</span>
      </div>
    </div>
  );
}
