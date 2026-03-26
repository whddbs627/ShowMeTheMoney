import { useState, useEffect, useCallback } from "react";
import { getBotStatus, getBalance, getTrades, getPnl, getWatchlist } from "./api";
import type { BotStatus, BalanceInfo, TradeRecord, PnlPoint } from "./types";
import AuthPage from "./components/AuthPage";
import StatusCard from "./components/StatusCard";
import PriceDisplay from "./components/PriceDisplay";
import BalanceCard from "./components/BalanceCard";
import BotControls from "./components/BotControls";
import TradeTable from "./components/TradeTable";
import PnlChart from "./components/PnlChart";
import CoinSearch from "./components/CoinSearch";
import Watchlist from "./components/Watchlist";
import TopGainers from "./components/TopGainers";
import Settings from "./components/Settings";
import Leaderboard from "./components/Leaderboard";
import LogViewer from "./components/LogViewer";
import "./App.css";

type Tab = "dashboard" | "market" | "settings" | "leaderboard" | "logs";

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [username, setUsername] = useState("");
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [balance, setBalance] = useState<BalanceInfo | null>(null);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [pnl, setPnl] = useState<PnlPoint[]>([]);
  const [watchlistTickers, setWatchlistTickers] = useState<string[]>([]);
  const [tab, setTab] = useState<Tab>("dashboard");

  const fetchFast = useCallback(async () => {
    try {
      setStatus(await getBotStatus() as BotStatus);
    } catch { /* ignore */ }
  }, []);

  const fetchSlow = useCallback(async () => {
    try {
      const [b, t, p] = await Promise.all([getBalance(), getTrades(), getPnl()]);
      setBalance(b as BalanceInfo);
      setTrades(t as TradeRecord[]);
      setPnl(p as PnlPoint[]);
    } catch { /* ignore */ }
  }, []);

  const fetchWatchlist = useCallback(async () => {
    try {
      const data = await getWatchlist();
      setWatchlistTickers(data.tickers);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchFast();
    fetchSlow();
    fetchWatchlist();
    const fast = setInterval(fetchFast, 5000);
    const slow = setInterval(fetchSlow, 30000);
    return () => { clearInterval(fast); clearInterval(slow); };
  }, [token, fetchFast, fetchSlow, fetchWatchlist]);

  const handleLogin = (t: string, u: string) => { setToken(t); setUsername(u); };
  const handleLogout = () => { localStorage.removeItem("token"); setToken(null); setUsername(""); };
  const handleAction = () => { setTimeout(() => { fetchFast(); fetchSlow(); }, 500); };

  if (!token) return <AuthPage onLogin={handleLogin} />;

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">ShowMeTheMoney</h1>
        <div className="header-right">
          <span style={{ color: "#888", fontSize: 13 }}>{username}</span>
          <button className="btn-logout" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <div className="tabs">
        {(["dashboard", "market", "settings", "leaderboard", "logs"] as Tab[]).map((t) => (
          <button key={t} className={`tab ${tab === t ? "tab-active" : ""}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
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

      {tab === "settings" && <Settings />}
      {tab === "leaderboard" && <Leaderboard />}
      {tab === "logs" && <LogViewer />}
    </div>
  );
}

export default App;
