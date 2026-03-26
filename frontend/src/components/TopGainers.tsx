import { useState, useEffect } from "react";
import { getTopGainers, getTopVolume, getTopPrice, addToWatchlist } from "../api";

interface CoinData {
  ticker: string; name: string; current_price: number; change_pct: number; volume_krw: number;
}

type SortMode = "gainers" | "volume" | "price";

const TABS: { key: SortMode; label: string }[] = [
  { key: "gainers", label: "급등" },
  { key: "volume", label: "거래대금" },
  { key: "price", label: "고가" },
];

interface Props {
  watchlist: string[];
  onAdd: () => void;
}

export default function MarketRanking({ watchlist, onAdd }: Props) {
  const [data, setData] = useState<CoinData[]>([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<SortMode>("gainers");

  const fetchData = async (m: SortMode) => {
    setLoading(true);
    try {
      const fn = m === "gainers" ? getTopGainers : m === "volume" ? getTopVolume : getTopPrice;
      setData(await fn(20) as CoinData[]);
    } catch { setData([]); }
    setLoading(false);
  };

  useEffect(() => { fetchData(mode); }, [mode]);
  useEffect(() => {
    const interval = setInterval(() => fetchData(mode), 60000);
    return () => clearInterval(interval);
  }, [mode]);

  const handleAdd = async (ticker: string) => { await addToWatchlist(ticker); onAdd(); };

  const formatVolume = (v: number) => {
    if (v >= 1e12) return `${(v / 1e12).toFixed(1)}조`;
    if (v >= 1e8) return `${(v / 1e8).toFixed(0)}억`;
    if (v >= 1e4) return `${(v / 1e4).toFixed(0)}만`;
    return v.toLocaleString();
  };

  return (
    <div className="card">
      <h3>
        시장 랭킹
        <button onClick={() => fetchData(mode)} style={{ marginLeft: 12, padding: "2px 10px", fontSize: 11, borderRadius: 4, border: "1px solid #333", background: "transparent", color: "#888", cursor: "pointer" }}>
          새로고침
        </button>
      </h3>

      <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setMode(t.key)}
            style={{
              padding: "5px 14px", fontSize: 12, borderRadius: 4, border: "none", cursor: "pointer",
              background: mode === t.key ? "#3b82f6" : "#16162a", color: mode === t.key ? "#fff" : "#888",
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {loading && data.length === 0 ? (
        <p style={{ color: "#888", fontSize: 13 }}>불러오는 중...</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>코인</th>
                <th>현재가</th>
                <th>등락률</th>
                <th>거래대금</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.map((g, i) => {
                const inWatchlist = watchlist.includes(g.ticker);
                return (
                  <tr key={g.ticker}>
                    <td style={{ color: "#888" }}>{i + 1}</td>
                    <td style={{ fontWeight: 600 }}>{g.name}</td>
                    <td>{g.current_price.toLocaleString()}</td>
                    <td style={{ color: g.change_pct >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                      {g.change_pct >= 0 ? "+" : ""}{g.change_pct.toFixed(2)}%
                    </td>
                    <td style={{ color: "#888" }}>{formatVolume(g.volume_krw)}</td>
                    <td>
                      <button onClick={() => handleAdd(g.ticker)} disabled={inWatchlist}
                        style={{ padding: "3px 10px", fontSize: 11, borderRadius: 4, border: "none", cursor: inWatchlist ? "default" : "pointer", background: inWatchlist ? "#333" : "#3b82f6", color: "#fff", opacity: inWatchlist ? 0.5 : 1 }}>
                        {inWatchlist ? "추가됨" : "+ 추가"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
