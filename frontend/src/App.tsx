import { useState, useEffect, useCallback } from "react";
import { getBotStatus, getBalance, getTrades, getPnl } from "./api";
import type { BotStatus, BalanceInfo, TradeRecord, PnlPoint } from "./types";
import StatusCard from "./components/StatusCard";
import PriceDisplay from "./components/PriceDisplay";
import BalanceCard from "./components/BalanceCard";
import BotControls from "./components/BotControls";
import TradeTable from "./components/TradeTable";
import PnlChart from "./components/PnlChart";
import "./App.css";

function App() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [balance, setBalance] = useState<BalanceInfo | null>(null);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [pnl, setPnl] = useState<PnlPoint[]>([]);

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

  useEffect(() => {
    fetchFast();
    fetchSlow();

    const fastInterval = setInterval(fetchFast, 5000);
    const slowInterval = setInterval(fetchSlow, 30000);

    return () => {
      clearInterval(fastInterval);
      clearInterval(slowInterval);
    };
  }, [fetchFast, fetchSlow]);

  const handleAction = () => {
    setTimeout(() => {
      fetchFast();
      fetchSlow();
    }, 500);
  };

  return (
    <div className="container">
      <h1 className="title">ShowMeTheMoney</h1>
      <div className="grid-top">
        <StatusCard status={status} />
        <BalanceCard balance={balance} />
        <BotControls running={status?.running ?? false} onAction={handleAction} />
      </div>
      <PriceDisplay coins={status?.coins ?? []} />
      <PnlChart data={pnl} />
      <TradeTable trades={trades} />
    </div>
  );
}

export default App;
