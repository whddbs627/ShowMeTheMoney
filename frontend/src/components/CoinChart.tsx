import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getChart } from "../api";

const TIMEFRAMES = [
  { label: "1시간", interval: "minute1", count: 60 },
  { label: "1일", interval: "minute60", count: 24 },
  { label: "7일", interval: "day", count: 7 },
  { label: "30일", interval: "day", count: 30 },
  { label: "90일", interval: "day", count: 90 },
];

interface Props {
  ticker: string;
  onClose: () => void;
}

export default function CoinChart({ ticker, onClose }: Props) {
  const [data, setData] = useState<{ date: string; close: number }[]>([]);
  const [tfIdx, setTfIdx] = useState(3); // default 30일
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const tf = TIMEFRAMES[tfIdx];
    getChart(ticker, tf.interval, tf.count)
      .then((d) => setData(d.map((r) => ({ date: r.date, close: r.close }))))
      .finally(() => setLoading(false));
  }, [ticker, tfIdx]);

  const change = data.length >= 2 ? ((data[data.length - 1].close - data[0].close) / data[0].close) * 100 : 0;
  const color = change >= 0 ? "#22c55e" : "#ef4444";
  const lastPrice = data.length > 0 ? data[data.length - 1].close : 0;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ width: 640 }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <div>
            <h3 style={{ color: "#f0f0f0", margin: 0, display: "inline" }}>{ticker.replace("KRW-", "")}</h3>
            <span style={{ color: "#888", fontSize: 12, marginLeft: 8 }}>{ticker}</span>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#888", fontSize: 18, cursor: "pointer" }}>x</button>
        </div>

        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: "#f0f0f0" }}>{lastPrice.toLocaleString()}원</span>
          <span style={{ color, fontSize: 14, marginLeft: 8 }}>{change >= 0 ? "+" : ""}{change.toFixed(2)}%</span>
        </div>

        <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
          {TIMEFRAMES.map((tf, i) => (
            <button key={tf.label} onClick={() => setTfIdx(i)}
              style={{
                padding: "4px 12px", fontSize: 11, borderRadius: 4, border: "none", cursor: "pointer",
                background: tfIdx === i ? "#3b82f6" : "#16162a", color: tfIdx === i ? "#fff" : "#888",
              }}>{tf.label}</button>
          ))}
        </div>

        {loading ? (
          <p style={{ color: "#888", textAlign: "center", padding: 40 }}>불러오는 중...</p>
        ) : data.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" fontSize={10} />
              <YAxis stroke="#888" fontSize={10} tickFormatter={(v) => v.toLocaleString()} domain={["auto", "auto"]} />
              <Tooltip contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333" }}
                formatter={(v) => [`${Number(v).toLocaleString()}원`, "가격"]} />
              <Area type="monotone" dataKey="close" stroke={color} fill={color + "22"} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <p style={{ color: "#888", textAlign: "center", padding: 40 }}>데이터 없음</p>
        )}
      </div>
    </div>
  );
}
