import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { PnlPoint } from "../types";

export default function PnlChart({ data }: { data: PnlPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="card">
        <h3>Cumulative P&L</h3>
        <p style={{ color: "#888" }}>No data yet.</p>
      </div>
    );
  }

  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.timestamp).toLocaleDateString("ko-KR"),
  }));

  const lastPnl = data[data.length - 1].cumulative_pnl_krw;

  return (
    <div className="card">
      <h3>
        Cumulative P&L{" "}
        <span style={{ color: lastPnl >= 0 ? "#22c55e" : "#ef4444", fontSize: 18 }}>
          {lastPnl >= 0 ? "+" : ""}
          {lastPnl.toLocaleString()} KRW
        </span>
      </h3>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="date" stroke="#888" fontSize={12} />
          <YAxis stroke="#888" fontSize={12} tickFormatter={(v) => `${v.toLocaleString()}`} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333" }}
            formatter={(value) => [`${Number(value).toLocaleString()} KRW`, "P&L"]}
          />
          <Area
            type="monotone"
            dataKey="cumulative_pnl_krw"
            stroke={lastPnl >= 0 ? "#22c55e" : "#ef4444"}
            fill={lastPnl >= 0 ? "#22c55e22" : "#ef444422"}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
