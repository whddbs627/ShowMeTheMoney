import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getChart } from "../api";

interface Props {
  ticker: string;
  onClose: () => void;
}

export default function CoinChart({ ticker, onClose }: Props) {
  const [data, setData] = useState<{ date: string; close: number }[]>([]);
  const [days, setDays] = useState(30);

  useEffect(() => {
    getChart(ticker, days).then((d) => setData(d.map((r) => ({ date: r.date, close: r.close }))));
  }, [ticker, days]);

  const change = data.length >= 2 ? ((data[data.length - 1].close - data[0].close) / data[0].close) * 100 : 0;
  const color = change >= 0 ? "#22c55e" : "#ef4444";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ width: 600 }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ color: "#f0f0f0", margin: 0 }}>
            {ticker.replace("KRW-", "")}
            <span style={{ color, fontSize: 14, marginLeft: 8 }}>{change >= 0 ? "+" : ""}{change.toFixed(2)}%</span>
          </h3>
          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
            {[7, 30, 90].map((d) => (
              <button key={d} onClick={() => setDays(d)}
                style={{
                  padding: "3px 10px", fontSize: 11, borderRadius: 4, border: "none", cursor: "pointer",
                  background: days === d ? "#3b82f6" : "#16162a", color: days === d ? "#fff" : "#888",
                }}>{d}일</button>
            ))}
            <button onClick={onClose} style={{ background: "none", border: "none", color: "#888", fontSize: 18, cursor: "pointer", marginLeft: 8 }}>x</button>
          </div>
        </div>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" fontSize={11} />
              <YAxis stroke="#888" fontSize={11} tickFormatter={(v) => v.toLocaleString()} domain={["auto", "auto"]} />
              <Tooltip contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333" }}
                formatter={(v) => [`${Number(v).toLocaleString()}원`, "종가"]} />
              <Area type="monotone" dataKey="close" stroke={color} fill={color + "22"} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <p style={{ color: "#888", textAlign: "center", padding: 40 }}>불러오는 중...</p>
        )}
      </div>
    </div>
  );
}
