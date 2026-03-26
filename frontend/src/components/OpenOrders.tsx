import { useState, useEffect } from "react";
import { getOpenOrders, cancelOrder } from "../api";

interface Order {
  uuid: string;
  side: string;
  ticker: string;
  price: number;
  volume: number;
  remaining: number;
  amount_krw: number;
  created_at: string;
}

interface Props {
  onCancel: () => void;
}

export default function OpenOrders({ onCancel }: Props) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [msg, setMsg] = useState("");

  const fetchOrders = async () => {
    try { setOrders(await getOpenOrders()); } catch { /* */ }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleCancel = async (uuid: string) => {
    setLoading((p) => ({ ...p, [uuid]: true }));
    try {
      await cancelOrder(uuid);
      setMsg("주문이 취소되었습니다");
      fetchOrders();
      onCancel();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "취소 실패");
    }
    setLoading((p) => ({ ...p, [uuid]: false }));
    setTimeout(() => setMsg(""), 3000);
  };

  if (orders.length === 0) return null;

  return (
    <div className="card">
      <h3>미체결 주문 ({orders.length}건)</h3>
      {msg && (
        <div style={{ background: msg.includes("실패") ? "#ef444422" : "#22c55e22", border: `1px solid ${msg.includes("실패") ? "#ef4444" : "#22c55e"}`, borderRadius: 6, padding: "6px 12px", marginBottom: 8, fontSize: 12, color: msg.includes("실패") ? "#ef4444" : "#22c55e" }}>
          {msg}
        </div>
      )}
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>코인</th>
              <th>구분</th>
              <th>주문가</th>
              <th>수량</th>
              <th>금액</th>
              <th>주문시간</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.uuid}>
                <td style={{ fontWeight: 600 }}>{o.ticker.replace("KRW-", "")}</td>
                <td style={{ color: o.side === "매수" ? "#22c55e" : "#ef4444", fontWeight: 600 }}>{o.side}</td>
                <td>{o.price.toLocaleString()}원</td>
                <td>{o.remaining.toFixed(6)}</td>
                <td>{o.amount_krw.toLocaleString()}원</td>
                <td style={{ fontSize: 11, color: "#888" }}>{new Date(o.created_at).toLocaleString("ko-KR")}</td>
                <td>
                  <button onClick={() => handleCancel(o.uuid)} disabled={loading[o.uuid]}
                    style={{ padding: "3px 8px", fontSize: 11, borderRadius: 4, border: "1px solid #ef4444", background: "transparent", color: "#ef4444", cursor: "pointer" }}>
                    {loading[o.uuid] ? "..." : "취소"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
