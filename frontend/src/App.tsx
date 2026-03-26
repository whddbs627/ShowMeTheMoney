import { useState, useEffect, useCallback } from "react";
import { getBotStatus, getBalance, getTrades, getPnl, getWatchlist } from "./api";
import type { BotStatus, BalanceInfo, TradeRecord, PnlPoint } from "./types";
import StatusCard from "./components/StatusCard";
import PriceDisplay from "./components/PriceDisplay";
import BalanceCard from "./components/BalanceCard";
import BotControls from "./components/BotControls";
import TradeTable from "./components/TradeTable";
import PnlChart from "./components/PnlChart";
import CoinSearch from "./components/CoinSearch";
import Watchlist from "./components/Watchlist";
import TopGainers from "./components/TopGainers";
import "./App.css";

function App() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [balance, setBalance] = useState<BalanceInfo | null>(null);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [pnl, setPnl] = useState<PnlPoint[]>([]);
  const [watchlistTickers, setWatchlistTickers] = useState<string[]>([]);
  const [tab, setTab] = useState<"dashboard" | "market">("dashboard");

  const fetchFast = useCallback(async () => {
    try {
      setStatus(await getBotStatus());
    } catch (e) {
      console.error("Failed to fetch status", e);
    }
  }, []);

  const fetchSlow = useCallback(async () => {
    try {
      const [b, t, pnlData] = await Promise.all([getBalance(), getTrades(), getPnl()]);
      setBalance(b);
      setTrades(t);
      setPnl(pnlData);
    } catch (e) {
      console.error("Failed to fetch data", e);
    }
  }, []);

  const fetchWatchlist = useCallback(async () => {
    try {
      const data = await getWatchlist();
      setWatchlistTickers(data.tickers);
    } catch (e) {
      console.error("Failed to fetch watchlist", e);
    }
  }, []);

  useEffect(() => {
    fetchFast();
    fetchSlow();
    fetchWatchlist();

    const fastInterval = setInterval(fetchFast, 5000);
    const slowInterval = setInterval(fetchSlow, 30000);

    return () => {
      clearInterval(fastInterval);
      clearInterval(slowInterval);
    };
  }, [fetchFast, fetchSlow, fetchWatchlist]);

  const handleAction = () => {
    setTimeout(() => {
      fetchFast();
      fetchSlow();
    }, 500);
  };

  return (
    <div className="container">
      <h1 className="title">ShowMeTheMoney</h1>

      <div className="tabs">
        <button
          className={`tab ${tab === "dashboard" ? "tab-active" : ""}`}
          onClick={() => setTab("dashboard")}
        >
          Dashboard
        </button>
        <button
          className={`tab ${tab === "market" ? "tab-active" : ""}`}
          onClick={() => setTab("market")}
        >
          Market
        </button>
      </div>

      {tab === "dashboard" && (
        <>
          <div className="grid-top">
            <StatusCard status={status} />
            <BalanceCard balance={balance} />
            <BotControls running={status?.running ?? false} onAction={handleAction} />
          </div>
          <PriceDisplay coins={status?.coins ?? []} />
          <PnlChart data={pnl} />
          <TradeTable trades={trades} />
        </>
      )}

      {tab === "market" && (
        <>
          <div className="grid-market">
            <CoinSearch watchlist={watchlistTickers} onAdd={fetchWatchlist} />
            <Watchlist tickers={watchlistTickers} onRemove={fetchWatchlist} />
          </div>
          <TopGainers watchlist={watchlistTickers} onAdd={fetchWatchlist} />
        </>
      )}
    </div>
  );
}

export default App;
