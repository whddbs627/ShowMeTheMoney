import { useState, useEffect } from "react";
import { getMe, saveApiKeys, saveDiscord } from "../api";

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function Settings({ open, onClose }: Props) {
  const [accessKey, setAccessKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [discordUrl, setDiscordUrl] = useState("");
  const [notifyBuy, setNotifyBuy] = useState(true);
  const [notifySell, setNotifySell] = useState(true);
  const [notifyError, setNotifyError] = useState(true);
  const [notifyStartStop, setNotifyStartStop] = useState(true);
  const [hasKeys, setHasKeys] = useState(false);
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    getMe().then((data) => {
      setHasKeys(data.has_api_keys);
      setDiscordUrl(data.discord_webhook_url);
      setNotifyBuy(data.notify_buy);
      setNotifySell(data.notify_sell);
      setNotifyError(data.notify_error);
      setNotifyStartStop(data.notify_start_stop);
    });
  }, [open]);

  if (!open) return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      if (accessKey && secretKey) {
        await saveApiKeys(accessKey, secretKey);
        setHasKeys(true); setAccessKey(""); setSecretKey("");
      }
      await saveDiscord(discordUrl, notifyBuy, notifySell, notifyError, notifyStartStop);
      setMsg("저장 완료!"); setTimeout(() => setMsg(""), 2000);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "저장 실패");
    }
    setSaving(false);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ color: "#f0f0f0", margin: 0, fontSize: 18 }}>설정</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#888", fontSize: 20, cursor: "pointer" }}>x</button>
        </div>

        {msg && (
          <div style={{ background: msg.includes("실패") ? "#ef444422" : "#22c55e22", border: `1px solid ${msg.includes("실패") ? "#ef4444" : "#22c55e"}`, borderRadius: 6, padding: "6px 12px", marginBottom: 12, fontSize: 12, color: msg.includes("실패") ? "#ef4444" : "#22c55e" }}>
            {msg}
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: "#ccc", fontSize: 13, margin: "0 0 8px" }}>
            업비트 API 키 {hasKeys ? <span style={{ color: "#22c55e" }}>저장됨</span> : <span style={{ color: "#ef4444" }}>미설정</span>}
          </h4>
          <input className="input" type="password" placeholder={hasKeys ? "변경 시 입력 (빈칸=유지)" : "Access Key"} value={accessKey} onChange={(e) => setAccessKey(e.target.value)} />
          <input className="input" type="password" placeholder={hasKeys ? "변경 시 입력 (빈칸=유지)" : "Secret Key"} value={secretKey} onChange={(e) => setSecretKey(e.target.value)} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: "#ccc", fontSize: 13, margin: "0 0 8px" }}>
            디스코드 알림 {discordUrl ? <span style={{ color: "#22c55e" }}>저장됨</span> : <span style={{ color: "#888" }}>선택</span>}
          </h4>
          <input className="input" type="text" placeholder="디스코드 웹훅 URL" value={discordUrl} onChange={(e) => setDiscordUrl(e.target.value)} />

          <p style={{ color: "#888", fontSize: 11, margin: "8px 0 4px" }}>받을 알림 선택:</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
            {[
              { label: "매수 알림", value: notifyBuy, set: setNotifyBuy },
              { label: "매도 알림", value: notifySell, set: setNotifySell },
              { label: "에러 알림", value: notifyError, set: setNotifyError },
              { label: "시작/중지 알림", value: notifyStartStop, set: setNotifyStartStop },
            ].map((item) => (
              <label key={item.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#aaa", cursor: "pointer" }}>
                <input type="checkbox" checked={item.value} onChange={(e) => item.set(e.target.checked)} />
                {item.label}
              </label>
            ))}
          </div>
        </div>

        <button className="btn btn-start" style={{ width: "100%", padding: 12 }} onClick={handleSave} disabled={saving}>
          {saving ? "저장 중..." : "설정 저장"}
        </button>
      </div>
    </div>
  );
}
