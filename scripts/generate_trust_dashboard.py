"""Generate the child-friendly Trust Score dashboard (a self-contained HTML file).

Reads trust-score/build-state.json (which sections are pending/in_progress/done),
runs the engine on a sample run so the page shows a real score, and writes
trust-score/dashboard.html. The page auto-refreshes, so a browser tab left open
updates itself every time this script is re-run as sections complete.

    python scripts/generate_trust_dashboard.py
"""

import json
from pathlib import Path

from scripts.trust_score import DEFAULT_CONFIG, compute_trust_score, load_config

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "trust-score" / "build-state.json"
OUTPUT_PATH = ROOT / "trust-score" / "dashboard.html"
CONFIG_PATH = ROOT / "config" / "trust-score.yml"

STATUS_STYLE = {
    "done": ("#1b7f4b", "#e3f6ec", "✅", "DONE"),
    "in_progress": ("#b26a00", "#fff4e0", "🔨", "WORKING ON IT"),
    "pending": ("#8a8a8a", "#f0f0f0", "⬜", "NOT STARTED YET"),
}

SAMPLE_SIGNALS = {
    "tests_pass": 1.0,
    "independent_verification": 1.0,
    "coverage": 0.92,
    "regression_clean": 1.0,
    "secret_scan_clean": 1.0,
    "production_health": 1.0,
}

SIGNAL_KID = {
    "tests_pass": "Did all the tests pass?",
    "independent_verification": "Did a DIFFERENT checker agree it works?",
    "coverage": "How much of the work was tested?",
    "regression_clean": "Did we break anything that used to work?",
    "secret_scan_clean": "Did we keep secrets safe?",
    "production_health": "Is it healthy after going live?",
}


def _progress(sections: list[dict]) -> int:
    done = sum(1 for s in sections if s["status"] == "done")
    return int(round(done / len(sections) * 100)) if sections else 0


def _section_cards(sections: list[dict]) -> str:
    cards = []
    for s in sections:
        color, bg, icon, label = STATUS_STYLE.get(s["status"], STATUS_STYLE["pending"])
        cards.append(f"""
        <div class="card" style="border-left:10px solid {color};background:{bg};">
          <div class="card-top">
            <span class="card-icon">{icon}</span>
            <span class="card-name" style="color:{color};">{s['id']}. {s['name']}</span>
            <span class="card-badge" style="background:{color};">{label}</span>
          </div>
          <div class="card-kid">{s['kid']}</div>
        </div>""")
    return "".join(cards)


def _signal_bars(signals: dict, weights: dict) -> str:
    bars = []
    for name, weight in weights.items():
        value = signals.get(name, 0.0)
        pct = int(round(value * 100))
        bars.append(f"""
        <div class="sig">
          <div class="sig-label">{SIGNAL_KID.get(name, name)} <em>(worth {int(weight*100)} points)</em></div>
          <div class="sig-track"><div class="sig-fill" style="width:{pct}%;"></div></div>
          <div class="sig-val">{pct}%</div>
        </div>""")
    return "".join(bars)


def render(state: dict, config: dict) -> str:
    sections = state["sections"]
    progress = _progress(sections)
    result = compute_trust_score(SAMPLE_SIGNALS, config)

    score = result["score"]
    gauge_color = "#1b7f4b" if score >= config["threshold"] else "#b26a00"
    rec = result["recommended"]
    eff = result["effective"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>Trust Score — what the robot is building</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Comic Sans MS', 'Segoe UI', sans-serif; margin:0; background:#fafbff; color:#222; }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 24px; }}
  h1 {{ font-size: 30px; margin: 0 0 6px; }}
  .motto {{ font-size: 18px; color:#3a3a9a; font-weight:bold; margin-bottom:18px; }}
  .panel {{ background:#fff; border-radius:18px; padding:20px; margin-bottom:20px;
            box-shadow:0 4px 14px rgba(0,0,0,0.06); }}
  .explain {{ font-size:17px; line-height:1.6; }}
  .progress-track {{ background:#eee; border-radius:20px; height:28px; overflow:hidden; margin-top:10px; }}
  .progress-fill {{ background:linear-gradient(90deg,#36b37e,#1b7f4b); height:100%;
                    width:{progress}%; transition:width .6s; }}
  .progress-num {{ text-align:right; font-weight:bold; font-size:15px; margin-top:4px; }}
  .card {{ border-radius:12px; padding:14px 16px; margin:12px 0; }}
  .card-top {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .card-icon {{ font-size:22px; }}
  .card-name {{ font-size:18px; font-weight:bold; flex:1; }}
  .card-badge {{ color:#fff; font-size:11px; font-weight:bold; padding:3px 8px; border-radius:20px; }}
  .card-kid {{ font-size:15px; margin-top:6px; color:#444; }}
  .gauge {{ text-align:center; }}
  .gauge-num {{ font-size:64px; font-weight:bold; color:{gauge_color}; }}
  .gauge-sub {{ font-size:15px; color:#666; }}
  .decision {{ display:inline-block; padding:8px 16px; border-radius:24px; font-weight:bold;
               font-size:16px; margin:6px 4px; }}
  .sig {{ display:flex; align-items:center; gap:10px; margin:8px 0; }}
  .sig-label {{ flex:1; font-size:14px; }}
  .sig-label em {{ color:#888; font-style:italic; }}
  .sig-track {{ width:130px; background:#eee; border-radius:10px; height:14px; overflow:hidden; }}
  .sig-fill {{ background:#4c8bf5; height:100%; }}
  .sig-val {{ width:42px; text-align:right; font-size:13px; font-weight:bold; }}
  .foot {{ font-size:13px; color:#999; text-align:center; margin-top:10px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>🤖 The Robot's Report Card</h1>
  <div class="motto">{state['motto']}</div>

  <div class="panel">
    <div class="explain">{state['child_explainer']}</div>
  </div>

  <div class="panel">
    <h2>How much is built?</h2>
    <div class="progress-track"><div class="progress-fill"></div></div>
    <div class="progress-num">{progress}% complete</div>
    {_section_cards(sections)}
  </div>

  <div class="panel gauge">
    <h2>What does a report card look like?</h2>
    <div class="gauge-num">{score}/100</div>
    <div class="gauge-sub">(this is a pretend run, so you can see how it works)</div>
    <div>
      <span class="decision" style="background:#e3f6ec;color:#1b7f4b;">Robot's wish: {rec}</span>
      <span class="decision" style="background:#fff4e0;color:#b26a00;">What really happens: {eff} 🧑 grown-up presses the button</span>
    </div>
    <p class="explain" style="text-align:left;margin-top:14px;">
      Even though the score is high and the robot would like to work alone (<b>{rec}</b>),
      we are in <b>shadow mode</b>, so a grown-up still decides every time (<b>{eff}</b>).
      We watch quietly until the report card has been honest for a long time.
    </p>
    <h3 style="text-align:left;">The points that make up the score</h3>
    {_signal_bars(SAMPLE_SIGNALS, config['weights'])}
  </div>

  <div class="foot">Last updated: {state['updated']} · this page refreshes itself every 15 seconds</div>
</div>
</body>
</html>
"""


def main() -> int:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    config = load_config(CONFIG_PATH) if CONFIG_PATH.exists() else DEFAULT_CONFIG
    OUTPUT_PATH.write_text(render(state, config), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH} ({_progress(state['sections'])}% complete)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
