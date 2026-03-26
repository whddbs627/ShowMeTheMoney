import { useState } from "react";
import { startBot, stopBot } from "../api";

interface Props {
  running: boolean;
  onAction: () => void;
}

export default function BotControls({ running, onAction }: Props) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setError("");
    setLoading(true);
    try {
      await startBot();
      onAction();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start failed");
    }
    setLoading(false);
  };

  const handleStop = async () => {
    setError("");
    setLoading(true);
    try {
      await stopBot();
      onAction();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    }
    setLoading(false);
  };

  return (
    <div className="card">
      <h3>Controls</h3>
      <div style={{ display: "flex", gap: 12 }}>
        <button className="btn btn-start" disabled={running || loading} onClick={handleStart}>
          {loading && !running ? "Starting..." : "Start"}
        </button>
        <button className="btn btn-stop" disabled={!running || loading} onClick={handleStop}>
          {loading && running ? "Stopping..." : "Stop"}
        </button>
      </div>
      {error && <p style={{ color: "#ef4444", fontSize: 12, marginTop: 8 }}>{error}</p>}
    </div>
  );
}
