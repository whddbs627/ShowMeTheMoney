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
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMe().then((data) => {
      setHasKeys(data.has_api_keys);
      setDiscordUrl(data.discord_webhook_url);
      setStrategy(data.strategy);
    });
  }, []);

  const showMsg = (text: string, isError = false) => {
    setMsg((isError ? "ERROR: " : "") + text);
    setTimeout(() => setMsg(""), 4000);
  };

  const handleSaveAll = async () => {
    setSaving(true);
    try {
      if (accessKey && secretKey) {
        await saveApiKeys(accessKey, secretKey);
        setHasKeys(true); setAccessKey(""); setSecretKey("");
      }
      await saveDiscord(discordUrl);
      await saveStrategy(strategy);
      showMsg("모든 설정이 저장되었습니다!");
    } catch (e) {
      showMsg(e instanceof Error ? e.message : "저장 실패", true);
    }
    setSaving(false);
  };

  return (
    <>
      {msg && (
        <div style={{
          background: msg.startsWith("ERROR") ? "#ef444422" : "#22c55e22",
          border: `1px solid ${msg.startsWith("ERROR") ? "#ef4444" : "#22c55e"}`,
          borderRadius: 8, padding: "8px 16px", marginBottom: 16,
          color: msg.startsWith("ERROR") ? "#ef4444" : "#22c55e", fontSize: 13,
        }}>{msg}</div>
      )}

      <div className="card">
        <h3>
          업비트 API 키
          {hasKeys
            ? <span style={{ color: "#22c55e", fontSize: 12, marginLeft: 8 }}>저장됨</span>
            : <span style={{ color: "#ef4444", fontSize: 12, marginLeft: 8 }}>미설정</span>}
        </h3>
        <input className="input" type="password" placeholder={hasKeys ? "변경하려면 입력 (빈칸이면 유지)" : "Access Key"} value={accessKey} onChange={(e) => setAccessKey(e.target.value)} />
        <input className="input" type="password" placeholder={hasKeys ? "변경하려면 입력 (빈칸이면 유지)" : "Secret Key"} value={secretKey} onChange={(e) => setSecretKey(e.target.value)} />
        <p style={{ color: "#666", fontSize: 11, marginTop: 4 }}>암호화(AES)되어 안전하게 저장됩니다.</p>
      </div>

      <div className="card">
        <h3>
          디스코드 알림
          {discordUrl
            ? <span style={{ color: "#22c55e", fontSize: 12, marginLeft: 8 }}>저장됨</span>
            : <span style={{ color: "#888", fontSize: 12, marginLeft: 8 }}>선택사항</span>}
        </h3>
        <input className="input" type="text" placeholder="디스코드 웹훅 URL" value={discordUrl} onChange={(e) => setDiscordUrl(e.target.value)} />
      </div>

      <div className="card">
        <h3>매매 전략</h3>
        <div className="setting-row">
          <label>K값 (변동성 돌파 계수)</label>
          <input type="number" step="0.1" min="0.1" max="1.0" value={strategy.k} onChange={(e) => setStrategy({ ...strategy, k: +e.target.value })} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>이동평균 필터 (5일선 &gt; 20일선)</label>
          <input type="checkbox" checked={strategy.use_ma} onChange={(e) => setStrategy({ ...strategy, use_ma: e.target.checked })} />
        </div>
        <div className="setting-row">
          <label>RSI 필터 (과매도 방지)</label>
          <input type="checkbox" checked={strategy.use_rsi} onChange={(e) => setStrategy({ ...strategy, use_rsi: e.target.checked })} />
        </div>
        <div className="setting-row">
          <label>RSI 하한값</label>
          <input type="number" step="5" min="10" max="50" value={strategy.rsi_lower} onChange={(e) => setStrategy({ ...strategy, rsi_lower: +e.target.value })} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>손절 비율</label>
          <input type="number" step="0.01" min="0.01" max="0.2" value={strategy.loss_pct} onChange={(e) => setStrategy({ ...strategy, loss_pct: +e.target.value })} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>코인당 최대 투자금 (원)</label>
          <input type="number" step="10000" min="5000" value={strategy.max_investment_krw} onChange={(e) => setStrategy({ ...strategy, max_investment_krw: +e.target.value })} className="input-sm" />
        </div>
      </div>

      <button className="btn btn-start" style={{ width: "100%", padding: 14, fontSize: 16 }}
        onClick={handleSaveAll} disabled={saving}>
        {saving ? "저장 중..." : "전체 설정 저장"}
      </button>
    </>
  );
}
