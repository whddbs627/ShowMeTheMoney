import { useState, useEffect } from "react";
import { getMe, saveStrategy } from "../api";

const PRESETS = [
  {
    name: "안정형",
    desc: "낮은 K값 + 모든 필터 ON. 매매 빈도 낮지만 안정적",
    config: { k: 0.3, use_ma: true, use_rsi: true, rsi_lower: 35, loss_pct: 0.02, max_investment_krw: 50000 },
  },
  {
    name: "균형형 (추천)",
    desc: "기본 설정. 변동성 돌파 + 추세/RSI 필터",
    config: { k: 0.5, use_ma: true, use_rsi: true, rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000 },
  },
  {
    name: "공격형",
    desc: "높은 K값 + 필터 최소화. 매매 빈도 높고 수익/손실 폭 큼",
    config: { k: 0.7, use_ma: false, use_rsi: false, rsi_lower: 20, loss_pct: 0.05, max_investment_krw: 200000 },
  },
  {
    name: "추세추종형",
    desc: "이동평균 필터만 사용. 상승 추세에서만 매수",
    config: { k: 0.5, use_ma: true, use_rsi: false, rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000 },
  },
  {
    name: "역발상형",
    desc: "RSI 과매도 구간 진입. 급락 후 반등 노림",
    config: { k: 0.4, use_ma: false, use_rsi: true, rsi_lower: 25, loss_pct: 0.04, max_investment_krw: 100000 },
  },
];

export default function Strategy() {
  const [strategy, setStrategy] = useState({
    k: 0.5, use_ma: true, use_rsi: true,
    rsi_lower: 30, loss_pct: 0.03, max_investment_krw: 100000,
  });
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  useEffect(() => {
    getMe().then((data) => setStrategy(data.strategy));
  }, []);

  const showMsg = (text: string) => { setMsg(text); setTimeout(() => setMsg(""), 3000); };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setStrategy(preset.config);
    setActivePreset(preset.name);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveStrategy(strategy);
      showMsg("전략이 저장되었습니다!");
    } catch (e) {
      showMsg(e instanceof Error ? e.message : "저장 실패");
    }
    setSaving(false);
  };

  return (
    <>
      {msg && (
        <div style={{ background: "#22c55e22", border: "1px solid #22c55e", borderRadius: 8, padding: "8px 16px", marginBottom: 16, color: "#22c55e", fontSize: 13 }}>
          {msg}
        </div>
      )}

      <div className="card">
        <h3>추천 전략</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 8 }}>
          {PRESETS.map((p) => (
            <button key={p.name} onClick={() => applyPreset(p)}
              style={{
                padding: "12px", borderRadius: 8, border: `1px solid ${activePreset === p.name ? "#3b82f6" : "#2a2a4a"}`,
                background: activePreset === p.name ? "#3b82f622" : "#16162a",
                cursor: "pointer", textAlign: "left",
              }}>
              <div style={{ fontWeight: 600, color: "#f0f0f0", fontSize: 14, marginBottom: 4 }}>
                {p.name}
              </div>
              <div style={{ color: "#888", fontSize: 11, lineHeight: 1.4 }}>{p.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>세부 설정</h3>
        <div className="setting-row">
          <label>K값 (변동성 계수, 0.1~1.0)</label>
          <input type="number" step="0.1" min="0.1" max="1.0" value={strategy.k} onChange={(e) => { setStrategy({ ...strategy, k: +e.target.value }); setActivePreset(null); }} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>이동평균 필터 (5일선 &gt; 20일선일 때만 매수)</label>
          <input type="checkbox" checked={strategy.use_ma} onChange={(e) => { setStrategy({ ...strategy, use_ma: e.target.checked }); setActivePreset(null); }} />
        </div>
        <div className="setting-row">
          <label>RSI 필터 (과매도 구간 진입 방지)</label>
          <input type="checkbox" checked={strategy.use_rsi} onChange={(e) => { setStrategy({ ...strategy, use_rsi: e.target.checked }); setActivePreset(null); }} />
        </div>
        <div className="setting-row">
          <label>RSI 하한값 (이 값 이하면 매수 안 함)</label>
          <input type="number" step="5" min="10" max="50" value={strategy.rsi_lower} onChange={(e) => { setStrategy({ ...strategy, rsi_lower: +e.target.value }); setActivePreset(null); }} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>손절 비율 (매수가 대비 하락 시 자동 매도)</label>
          <input type="number" step="0.01" min="0.01" max="0.2" value={strategy.loss_pct} onChange={(e) => { setStrategy({ ...strategy, loss_pct: +e.target.value }); setActivePreset(null); }} className="input-sm" />
        </div>
        <div className="setting-row">
          <label>코인당 최대 투자금 (원)</label>
          <input type="number" step="10000" min="5000" value={strategy.max_investment_krw} onChange={(e) => { setStrategy({ ...strategy, max_investment_krw: +e.target.value }); setActivePreset(null); }} className="input-sm" />
        </div>
        <button className="btn btn-start" style={{ width: "100%", marginTop: 12, padding: 12 }}
          onClick={handleSave} disabled={saving}>
          {saving ? "저장 중..." : "전략 저장"}
        </button>
      </div>
    </>
  );
}
