import type { BotStatus, BalanceInfo, TradeRecord, PnlPoint } from "./types";

const BASE = "/api";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, options);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const getBotStatus = () => fetchJSON<BotStatus>("/bot/status");
export const startBot = () => fetchJSON<{ message: string }>("/bot/start", { method: "POST" });
export const stopBot = () => fetchJSON<{ message: string }>("/bot/stop", { method: "POST" });
export const getBalance = () => fetchJSON<BalanceInfo>("/balance");
export const getTrades = (limit = 50) => fetchJSON<TradeRecord[]>(`/trades?limit=${limit}`);
export const getPnl = () => fetchJSON<PnlPoint[]>("/trades/pnl");

// Market
export const searchCoins = (q = "") => fetchJSON<{ ticker: string; name: string }[]>(`/market/coins?q=${q}`);
export const getTopGainers = (limit = 20) =>
  fetchJSON<{ ticker: string; name: string; current_price: number; change_pct: number }[]>(
    `/market/top-gainers?limit=${limit}`
  );

// Watchlist
export const getWatchlist = () => fetchJSON<{ tickers: string[] }>("/watchlist");
export const addToWatchlist = (ticker: string) =>
  fetchJSON<{ message: string }>("/watchlist/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });
export const removeFromWatchlist = (ticker: string) =>
  fetchJSON<{ message: string }>("/watchlist/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });
