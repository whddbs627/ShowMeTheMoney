import { removeFromWatchlist } from "../api";

interface Props {
  tickers: string[];
  onRemove: () => void;
}

export default function Watchlist({ tickers, onRemove }: Props) {
  const handleRemove = async (ticker: string) => {
    await removeFromWatchlist(ticker);
    onRemove();
  };

  return (
    <div className="card">
      <h3>Watchlist ({tickers.length} coins)</h3>
      {tickers.length === 0 ? (
        <p style={{ color: "#888", fontSize: 13 }}>No coins added. Search and add coins above.</p>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {tickers.map((ticker) => (
            <div
              key={ticker}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                background: "#16162a",
                borderRadius: 20,
                fontSize: 13,
              }}
            >
              <span style={{ fontWeight: 600 }}>{ticker.replace("KRW-", "")}</span>
              <button
                onClick={() => handleRemove(ticker)}
                style={{
                  background: "none",
                  border: "none",
                  color: "#ef4444",
                  cursor: "pointer",
                  fontSize: 14,
                  padding: 0,
                  lineHeight: 1,
                }}
              >
                x
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
