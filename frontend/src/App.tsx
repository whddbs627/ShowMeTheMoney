import { useState, useEffect, useCallback } from "react";
import { getBotStatus, getBalance, getTrades, getPnl, getWatchlist, getMe, getPrice } from "./api";
import type { BotStatus, BalanceInfo, TradeRecord, PnlPoint, CoinStatus } from "./types";
import AuthPage from "./components/AuthPage";
import StatusCard from "./components/StatusCard";
import PriceDisplay from "./components/PriceDisplay";
import BalanceCard from "./components/BalanceCard";
import TradeTable from "./components/TradeTable";
import PnlChart from "./components/PnlChart";
import CoinSearch from "./components/CoinSearch";
import TopGainers from "./components/TopGainers";
import Settings from "./components/Settings";
import Leaderboard from "./components/Leaderboard";
import "./App.css";

type Tab = "dashboard" | "trades" | "leaderboard";

const TAB_LABELS: Record<Tab, string> = {
  dashboard: "대시보드",
  trades: "매매 내역",
  leaderboard: "순위",
};

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [username, setUsername] = useState("");
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [coins, setCoins] = useState<CoinStatus[]>([]);
  const [balance, setBalance] = useState<BalanceInfo | null>(null);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [pnl, setPnl] = useState<PnlPoint[]>([]);
  const [watchlistTickers, setWatchlistTickers] = useState<string[]>([]);
  const [lossPct, setLossPct] = useState(0.03);
  const [tab, setTab] = useState<Tab>("dashboard");
  const [showSettings, setShowSettings] = useState(false);

  const fetchFast = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([getBotStatus(), getPrice()]);
      setStatus(s as BotStatus);
      setCoins((p as { coins: CoinStatus[] }).coins || []);
    } catch { /* */ }
  }, []);

  const fetchSlow = useCallback(async () => {
    try {
      const [b, t, p] = await Promise.all([getBalance(), getTrades(), getPnl()]);
      setBalance(b as BalanceInfo); setTrades(t as TradeRecord[]); setPnl(p as PnlPoint[]);
    } catch { /* */ }
  }, []);

  const fetchWatchlist = useCallback(async () => {
    try { setWatchlistTickers((await getWatchlist()).tickers); } catch { /* */ }
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchFast(); fetchSlow(); fetchWatchlist();
    getMe().then((data) => { setUsername(data.username); setLossPct(data.strategy.loss_pct); }).catch(() => {});
    const fast = setInterval(fetchFast, 5000);
    const slow = setInterval(fetchSlow, 30000);
    return () => { clearInterval(fast); clearInterval(slow); };
  }, [token, fetchFast, fetchSlow, fetchWatchlist]);

  const handleLogin = (t: string, u: string) => { setToken(t); setUsername(u); };
  const handleLogout = () => { localStorage.removeItem("token"); setToken(null); setUsername(""); };
  const handleAction = () => { setTimeout(() => { fetchFast(); fetchSlow(); }, 500); };
  const handleTrade = () => { fetchFast(); fetchSlow(); };

  if (!token) return <AuthPage onLogin={handleLogin} />;

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">ShowMeTheMoney</h1>
        <div className="header-right">
          <span style={{ color: "#888", fontSize: 13 }}>{username}</span>
          <button className="btn-icon" onClick={() => setShowSettings(!showSettings)} title="설정">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
          </button>
          <button className="btn-logout" onClick={handleLogout}>로그아웃</button>
        </div>
      </div>

      {showSettings && <div style={{ marginBottom: 16 }}><Settings /></div>}

      <div className="tabs">
        {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
          <button key={t} className={`tab ${tab === t ? "tab-active" : ""}`} onClick={() => setTab(t)}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {tab === "dashboard" && (
        <>
          <div className="grid-two">
            <StatusCard status={status} onAction={handleAction} />
            <BalanceCard balance={balance} pnl={pnl} />
          </div>
          <PriceDisplay coins={coins} watchlist={watchlistTickers} onRemove={fetchWatchlist} onTrade={handleTrade} lossPct={lossPct} />
          <CoinSearch watchlist={watchlistTickers} onAdd={fetchWatchlist} />
          <TopGainers watchlist={watchlistTickers} onAdd={fetchWatchlist} />
        </>
      )}

      {tab === "trades" && (
        <>
          <PnlChart data={pnl} />
          <TradeTable trades={trades} />
        </>
      )}

      {tab === "leaderboard" && <Leaderboard />}
    </div>
  );
}

export default App;
