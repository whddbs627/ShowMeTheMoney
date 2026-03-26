import { useState, useEffect } from "react";
import { searchCoins, addToWatchlist } from "../api";

interface Props {
  watchlist: string[];
  onAdd: () => void;
}

export default function CoinSearch({ watchlist, onAdd }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ ticker: string; name: string }[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length === 0) {
        setResults([]);
        return;
      }
      setLoading(true);
      try {
        const data = await searchCoins(query);
        setResults(data);
      } catch {
        setResults([]);
      }
      setLoading(false);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const handleAdd = async (ticker: string) => {
    await addToWatchlist(ticker);
    onAdd();
  };

  return (
    <div className="card">
      <h3>Coin Search</h3>
      <input
        type="text"
        placeholder="Search coin (e.g. BTC, ETH, SOL...)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{
          width: "100%",
          padding: "10px 12px",
          background: "#0f0f23",
          border: "1px solid #2a2a4a",
          borderRadius: 8,
          color: "#f0f0f0",
          fontSize: 14,
          marginBottom: 8,
          boxSizing: "border-box",
        }}
      />
      {loading && <p style={{ color: "#888", fontSize: 13 }}>Searching...</p>}
      {results.length > 0 && (
        <div style={{ maxHeight: 200, overflowY: "auto" }}>
          {results.map((coin) => {
            const inWatchlist = watchlist.includes(coin.ticker);
            return (
              <div
                key={coin.ticker}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "6px 0",
                  borderBottom: "1px solid #1a1a3e",
                }}
              >
                <span style={{ fontSize: 13 }}>
                  <strong>{coin.name}</strong>{" "}
                  <span style={{ color: "#888" }}>{coin.ticker}</span>
                </span>
                <button
                  onClick={() => handleAdd(coin.ticker)}
                  disabled={inWatchlist}
                  style={{
                    padding: "4px 12px",
                    fontSize: 12,
                    borderRadius: 6,
                    border: "none",
                    cursor: inWatchlist ? "default" : "pointer",
                    background: inWatchlist ? "#333" : "#3b82f6",
                    color: "#fff",
                    opacity: inWatchlist ? 0.5 : 1,
                  }}
                >
                  {inWatchlist ? "Added" : "+ Add"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
