import { startBot, stopBot } from "../api";

interface Props {
  running: boolean;
  onAction: () => void;
}

export default function BotControls({ running, onAction }: Props) {
  const handleStart = async () => {
    await startBot();
    onAction();
  };

  const handleStop = async () => {
    await stopBot();
    onAction();
  };

  return (
    <div className="card">
      <h3>Controls</h3>
      <div style={{ display: "flex", gap: 12 }}>
        <button className="btn btn-start" disabled={running} onClick={handleStart}>
          Start
        </button>
        <button className="btn btn-stop" disabled={!running} onClick={handleStop}>
          Stop
        </button>
      </div>
    </div>
  );
}
