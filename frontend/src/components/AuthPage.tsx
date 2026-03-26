import { useState } from "react";
import { login, register } from "../api";

interface Props {
  onLogin: (token: string, username: string) => void;
}

export default function AuthPage({ onLogin }: Props) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const data = await (isRegister ? register : login)(username, password);
      localStorage.setItem("token", data.token);
      onLogin(data.token, data.username);
    } catch (err) {
      setError(err instanceof Error ? err.message : "실패");
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      <div className="card" style={{ width: 360, margin: 0 }}>
        <h2 style={{ color: "#f0f0f0", marginBottom: 20, fontSize: 22, textAlign: "center" }}>ShowMeTheMoney</h2>
        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="아이디" value={username} onChange={(e) => setUsername(e.target.value)} className="input" />
          <input type="password" placeholder="비밀번호" value={password} onChange={(e) => setPassword(e.target.value)} className="input" />
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
