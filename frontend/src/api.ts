const BASE = "/api";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options?.body) headers["Content-Type"] = "application/json";

  const res = await fetch(`${BASE}${url}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.reload();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// Auth
export const register = (username: string, password: string) =>
  fetchJSON<{ token: string; username: string }>("/auth/register", {
    method: "POST", body: JSON.stringify({ username, password }),
  });

export const login = (username: string, password: string) =>
  fetchJSON<{ token: string; username: string }>("/auth/login", {
    method: "POST", body: JSON.stringify({ username, password }),
  });

export const getMe = () => fetchJSON<{
  user_id: number; username: string; has_api_keys: boolean;
  discord_webhook_url: string;
  strategy: { k: number; use_ma: boolean; use_rsi: boolean; rsi_lower: number; loss_pct: number; max_investment_krw: number };
}>("/auth/me");

export const saveApiKeys = (access_key: string, secret_key: string) =>
  fetchJSON<{ message: string }>("/auth/api-keys", {
    method: "POST", body: JSON.stringify({ access_key, secret_key }),
  });

export const saveDiscord = (webhook_url: string) =>
  fetchJSON<{ message: string }>("/auth/discord", {
    method: "POST", body: JSON.stringify({ webhook_url }),
  });

export const saveStrategy = (strategy: Record<string, unknown>) =>
  fetchJSON<{ message: string }>("/auth/strategy", {
    method: "POST", body: JSON.stringify(strategy),
  });

// Bot
export const getBotStatus = () => fetchJSON<{ running: boolean; uptime_seconds: number | null; coins: unknown[] }>("/bot/status");
export const startBot = () => fetchJSON<{ message: string }>("/bot/start", { method: "POST" });
export const stopBot = () => fetchJSON<{ message: string }>("/bot/stop", { method: "POST" });
export const getPrice = () => fetchJSON<{ coins: unknown[] }>("/price");

// Data
export const getBalance = () => fetchJSON<{ krw_balance: number | null; coins: unknown[]; total_krw: number | null }>("/balance");
export const getTrades = (limit = 50) => fetchJSON<unknown[]>(`/trades?limit=${limit}`);
export const getPnl = () => fetchJSON<unknown[]>("/trades/pnl");

// Manual orders
export const manualBuy = (ticker: string, amount_krw: number) =>
  fetchJSON<{ message: string; price: number }>("/order/buy", {
    method: "POST", body: JSON.stringify({ ticker, amount_krw }),
  });
export const manualSell = (ticker: string) =>
  fetchJSON<{ message: string; price: number; pnl_pct: number }>("/order/sell", {
    method: "POST", body: JSON.stringify({ ticker, sell_all: true }),
  });

// Market (no auth needed for search/gainers)
export const searchCoins = (q = "") => fetchJSON<{ ticker: string; name: string }[]>(`/market/coins?q=${q}`);
export const getTopGainers = (limit = 20) => fetchJSON<unknown[]>(`/market/top-gainers?limit=${limit}`);

// Watchlist
export const getWatchlist = () => fetchJSON<{ tickers: string[] }>("/watchlist");
export const addToWatchlist = (ticker: string) =>
  fetchJSON<{ message: string }>("/watchlist/add", {
    method: "POST", body: JSON.stringify({ ticker }),
  });
export const removeFromWatchlist = (ticker: string) =>
  fetchJSON<{ message: string }>("/watchlist/remove", {
    method: "POST", body: JSON.stringify({ ticker }),
  });

// Leaderboard
export const getLeaderboard = () => fetchJSON<{
  username: string; total_trades: number; total_pnl_krw: number; avg_pnl_pct: number;
}[]>("/leaderboard");
