import { useState, useEffect } from "react";
import { getMe, saveApiKeys, saveDiscord, saveStrategy } from "../api";

export default function Settings() {
  const [accessKey, setAccessKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [discordUrl, setDiscordUrl] = useState("");
  const [strategy, setStrategy] = useState({
    k: 0.5, use_ma: true, use_rsi: true,
    rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000,
  });
  const [hasKeys, setHasKeys] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getMe().then((data) => {
      setHasKeys(data.has_api_keys);
      setDiscordUrl(data.discord_webhook_url);
      setStrategy(data.strategy);
    });
  }, []);

  const showMsg = (text: string) => { setMsg(text); setTimeout(() => setMsg(""), 3000); };

  const handleSaveKeys = async () => {
    if (!accessKey || !secretKey) return;
    await saveApiKeys(accessKey, secretKey);
    setHasKeys(true);
    setAccessKey(""); setSecretKey("");
    showMsg("API keys saved (encrypted)");
  };

  const handleSaveDiscord = async () => {
    await saveDiscord(discordUrl);
    showMsg("Discord webhook saved");
  };

  const handleSaveStrategy = async () => {
    await saveStrategy(strategy);
    showMsg("Strategy saved");
  };

  return (
    <>
      {msg && (
        <div style={{ background: "#22c55e22", border: "1px solid #22c55e", borderRadius: 8, padding: "8px 16px", marginBottom: 16, color: "#22c55e", fontSize: 13 }}>
          {msg}
        </div>
      )}

      <div className="card">
        <h3>Upbit API Keys {hasKeys && <span style={{ color: "#22c55e", fontSize: 12 }}>Configured</span>}</h3>
        <input className="input" type="password" placeholder="Access Key" value={accessKey} onChange={(e) => setAccessKey(e.target.value)} />
        <input className="input" type="password" placeholder="Secret Key" value={secretKey} onChange={(e) => setSecretKey(e.target.value)} />
        <button className="btn btn-start" style={{ width: "100%", marginTop: 4 }} onClick={handleSaveKeys}>
          Save API Keys
        </button>
        <p style={{ color: "#888", fontSize: 11, marginTop: 8 }}>Keys are encrypted before storage.</p>
      </div>

      <div className="card">
        <h3>Discord Notification</h3>
        <input className="input" type="text" placeholder="Discord Webhook URL" value={discordUrl} onChange={(e) => setDiscordUrl(e.target.value)} />
        <button className="btn btn-start" style={{ width: "100%", marginTop: 4 }} onClick={handleSaveDiscord}>
          Save Webhook
        </button>
      </div>

      <div className="card">
        <h3>Trading Strategy</h3>
        <div className="setting-row">
          <label>K Value (Volatility)</label>
          <input type="number" step="0.1" min="0.1" max="1.0" value={strategy.k} onChange={(e) => setStrategy({ ...strategy, k: +e.target.value })} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>MA Filter (5MA &gt; 20MA)</label>
          <input type="checkbox" checked={strategy.use_ma} onChange={(e) => setStrategy({ ...strategy, use_ma: e.target.checked })} />
        </div>
        <div className="setting-row">
          <label>RSI Filter</label>
          <input type="checkbox" checked={strategy.use_rsi} onChange={(e) => setStrategy({ ...strategy, use_rsi: e.target.checked })} />
        </div>
        <div className="setting-row">
          <label>RSI Lower Bound</label>
          <input type="number" step="5" min="10" max="50" value={strategy.rsi_lower} onChange={(e) => setStrategy({ ...strategy, rsi_lower: +e.target.value })} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>Stop Loss %</label>
          <input type="number" step="0.01" min="0.01" max="0.2" value={strategy.loss_pct} onChange={(e) => setStrategy({ ...strategy, loss_pct: +e.target.value })} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>Max Investment (KRW/coin)</label>
          <input type="number" step="10000" min="5000" value={strategy.max_investment_krw} onChange={(e) => setStrategy({ ...strategy, max_investment_krw: +e.target.value })} className="input-sm" />
        </div>
        <button className="btn btn-start" style={{ width: "100%", marginTop: 8 }} onClick={handleSaveStrategy}>
          Save Strategy
        </button>
      </div>
    </>
  );
}
