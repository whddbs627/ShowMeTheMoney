import { useState, useEffect } from "react";
import { getTopGainers, addToWatchlist } from "../api";

interface Gainer {
  ticker: string;
  name: string;
  current_price: number;
  change_pct: number;
}

interface Props {
  watchlist: string[];
  onAdd: () => void;
}

export default function TopGainers({ watchlist, onAdd }: Props) {
  const [gainers, setGainers] = useState<Gainer[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchGainers = async () => {
    setLoading(true);
    try {
      setGainers(await getTopGainers(20) as Gainer[]);
    } catch {
      setGainers([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchGainers();
    const interval = setInterval(fetchGainers, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleAdd = async (ticker: string) => {
    await addToWatchlist(ticker);
    onAdd();
  };

  return (
    <div className="card">
      <h3>
        Top Gainers (24h)
        <button
          onClick={fetchGainers}
          style={{
            marginLeft: 12,
            padding: "2px 10px",
            fontSize: 11,
            borderRadius: 4,
            border: "1px solid #333",
            background: "transparent",
            color: "#888",
            cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </h3>
      {loading && gainers.length === 0 ? (
        <p style={{ color: "#888", fontSize: 13 }}>Loading market data...</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Coin</th>
                <th>Price</th>
                <th>Change</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {gainers.map((g, i) => {
                const inWatchlist = watchlist.includes(g.ticker);
                return (
                  <tr key={g.ticker}>
                    <td style={{ color: "#888" }}>{i + 1}</td>
                    <td style={{ fontWeight: 600 }}>{g.name}</td>
                    <td>{g.current_price.toLocaleString()}</td>
                    <td
                      style={{
                        color: g.change_pct >= 0 ? "#22c55e" : "#ef4444",
                        fontWeight: 600,
                      }}
                    >
                      {g.change_pct >= 0 ? "+" : ""}
                      {g.change_pct.toFixed(2)}%
                    </td>
                    <td>
                      <button
                        onClick={() => handleAdd(g.ticker)}
                        disabled={inWatchlist}
                        style={{
                          padding: "3px 10px",
                          fontSize: 11,
                          borderRadius: 4,
                          border: "none",
                          cursor: inWatchlist ? "default" : "pointer",
                          background: inWatchlist ? "#333" : "#3b82f6",
                          color: "#fff",
                          opacity: inWatchlist ? 0.5 : 1,
                        }}
                      >
                        {inWatchlist ? "Added" : "+ Add"}
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
