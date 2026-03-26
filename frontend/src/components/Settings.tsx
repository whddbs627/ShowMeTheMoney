import { useState, useEffect } from "react";
import { getMe, saveApiKeys, saveDiscord } from "../api";

export default function Settings() {
  const [accessKey, setAccessKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [discordUrl, setDiscordUrl] = useState("");
  const [hasKeys, setHasKeys] = useState(false);
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMe().then((data) => {
      setHasKeys(data.has_api_keys);
      setDiscordUrl(data.discord_webhook_url);
    });
  }, []);

  const showMsg = (text: string, isError = false) => {
    setMsg((isError ? "ERROR: " : "") + text);
    setTimeout(() => setMsg(""), 4000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (accessKey && secretKey) {
        await saveApiKeys(accessKey, secretKey);
        setHasKeys(true); setAccessKey(""); setSecretKey("");
      }
      await saveDiscord(discordUrl);
      showMsg("설정이 저장되었습니다!");
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
          {hasKeys ? <span style={{ color: "#22c55e", fontSize: 12, marginLeft: 8 }}>저장됨</span>
            : <span style={{ color: "#ef4444", fontSize: 12, marginLeft: 8 }}>미설정</span>}
        </h3>
        <input className="input" type="password" placeholder={hasKeys ? "변경하려면 입력 (빈칸이면 유지)" : "Access Key"} value={accessKey} onChange={(e) => setAccessKey(e.target.value)} />
        <input className="input" type="password" placeholder={hasKeys ? "변경하려면 입력 (빈칸이면 유지)" : "Secret Key"} value={secretKey} onChange={(e) => setSecretKey(e.target.value)} />
        <p style={{ color: "#666", fontSize: 11, marginTop: 4 }}>암호화(AES)되어 안전하게 저장됩니다.</p>
      </div>

      <div className="card">
        <h3>
          디스코드 알림
          {discordUrl ? <span style={{ color: "#22c55e", fontSize: 12, marginLeft: 8 }}>저장됨</span>
            : <span style={{ color: "#888", fontSize: 12, marginLeft: 8 }}>선택사항</span>}
        </h3>
        <input className="input" type="text" placeholder="디스코드 웹훅 URL" value={discordUrl} onChange={(e) => setDiscordUrl(e.target.value)} />
      </div>

      <button className="btn btn-start" style={{ width: "100%", padding: 14, fontSize: 16 }}
        onClick={handleSave} disabled={saving}>
        {saving ? "저장 중..." : "설정 저장"}
      </button>
    </>
  );
}
