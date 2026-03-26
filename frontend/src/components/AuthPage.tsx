import { useState } from "react";
import { login, register, saveApiKeys } from "../api";

interface Props {
  onLogin: (token: string, username: string) => void;
}

export default function AuthPage({ onLogin }: Props) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [accessKey, setAccessKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      if (isRegister) {
        const data = await register(username, password);
        localStorage.setItem("token", data.token);
        // API 키 입력된 경우 저장
        if (accessKey && secretKey) {
          await saveApiKeys(accessKey, secretKey);
        }
        onLogin(data.token, data.username);
      } else {
        const data = await login(username, password);
        localStorage.setItem("token", data.token);
        onLogin(data.token, data.username);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "실패");
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      <div className="card" style={{ width: 400, margin: 0 }}>
        <h2 style={{ color: "#f0f0f0", marginBottom: 4, fontSize: 24, textAlign: "center" }}>ShowMeTheMoney</h2>
        <p style={{ color: "#666", fontSize: 12, textAlign: "center", marginBottom: 20 }}>코인 자동매매 플랫폼</p>

        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="아이디" value={username} onChange={(e) => setUsername(e.target.value)} className="input" />
          <input type="password" placeholder="비밀번호" value={password} onChange={(e) => setPassword(e.target.value)} className="input" />

          {isRegister && (
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #2a2a4a" }}>
              <p style={{ color: "#888", fontSize: 12, marginBottom: 8 }}>업비트 API 키 (나중에 설정 가능)</p>
              <input type="password" placeholder="Access Key" value={accessKey} onChange={(e) => setAccessKey(e.target.value)} className="input" />
              <input type="password" placeholder="Secret Key" value={secretKey} onChange={(e) => setSecretKey(e.target.value)} className="input" />
            </div>
          )}

          {error && <p style={{ color: "#ef4444", fontSize: 13, margin: "8px 0" }}>{error}</p>}
          <button type="submit" className="btn btn-start" style={{ width: "100%", marginTop: 8 }} disabled={loading}>
            {loading ? "..." : isRegister ? "회원가입" : "로그인"}
          </button>
        </form>
        <p style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "#888" }}>
          {isRegister ? "이미 계정이 있나요?" : "계정이 없나요?"}{" "}
          <span style={{ color: "#3b82f6", cursor: "pointer" }}
            onClick={() => { setIsRegister(!isRegister); setError(""); }}>
            {isRegister ? "로그인" : "회원가입"}
          </span>
        </p>
      </div>
    </div>
  );
}
