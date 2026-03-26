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
    setError("");
    setLoading(true);

    try {
      const fn = isRegister ? register : login;
      const data = await fn(username, password);
      localStorage.setItem("token", data.token);
      onLogin(data.token, data.username);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      <div className="card" style={{ width: 360, margin: 0 }}>
        <h2 style={{ color: "#f0f0f0", marginBottom: 20, fontSize: 22, textAlign: "center" }}>
          ShowMeTheMoney
        </h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
          />
          {error && <p style={{ color: "#ef4444", fontSize: 13, margin: "8px 0" }}>{error}</p>}
          <button type="submit" className="btn btn-start" style={{ width: "100%", marginTop: 8 }} disabled={loading}>
            {loading ? "..." : isRegister ? "Register" : "Login"}
          </button>
        </form>
        <p style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "#888" }}>
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <span
            style={{ color: "#3b82f6", cursor: "pointer" }}
            onClick={() => { setIsRegister(!isRegister); setError(""); }}
          >
            {isRegister ? "Login" : "Register"}
          </span>
        </p>
      </div>
    </div>
  );
}
