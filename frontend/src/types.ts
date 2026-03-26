export interface CoinStatus {
  ticker: string;
  state: "holding" | "waiting";
  current_price: number | null;
  target_price: number | null;
  buy_price: number | null;
  rsi: number | null;
  ma_bullish: boolean | null;
}

export interface BotStatus {
  running: boolean;
  uptime_seconds: number | null;
  coins: CoinStatus[];
}

export interface CoinBalance {
  ticker: string;
  balance: number;
  price: number;
  value_krw: number;
}

export interface BalanceInfo {
  krw_balance: number | null;
  coins: CoinBalance[];
  total_krw: number | null;
}

export interface TradeRecord {
  id: number;
  timestamp: string;
  side: "BUY" | "SELL";
  ticker: string;
  price: number;
  amount_krw: number;
  reason: string | null;
  pnl_pct: number | null;
  pnl_krw: number | null;
}

export interface PnlPoint {
  timestamp: string;
  cumulative_pnl_krw: number;
}
