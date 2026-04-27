#!/usr/bin/env python3
"""
Scout Weekly Digest — generates a markdown briefing Stephen can read in 5
minutes Monday morning, suitable for emailing or pasting into Substack.

Reads:
  data/scout_briefing_auto.json  (top picks + briefings)
  data/podcast_signals_auto.json (raw episode feed for manual scanning)

Writes:
  data/scout_weekly_digest.md    (markdown digest)
  data/scout_weekly_digest.json  (machine-readable for email-sender script)

Design philosophy: a great headhunter doesn't dump a queue on you. They
hand you a 1-page memo: "5 finds you should know about, here's why."
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_MD = DATA / "scout_weekly_digest.md"
OUT_JSON = DATA / "scout_weekly_digest.json"


def main():
    briefing_path = DATA / "scout_briefing_auto.json"
    if not briefing_path.exists():
        print("⚠ scout_briefing_auto.json missing. Run scout_top_picks.py first.")
        return 1
    briefing = json.load(open(briefing_path))

    # Optional: raw podcast episodes for manual scanning section
    pod_path = DATA / "podcast_signals_auto.json"
    raw_episodes = []
    if pod_path.exists():
        pod = json.load(open(pod_path))
        raw_episodes = pod.get("rawEpisodes", [])[:10]

    week_of = briefing.get("weekOf") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = briefing.get("summary", {})
    picks = briefing.get("topPicks", [])
    runners = briefing.get("runnersUp", [])

    md_lines = []
    md_lines.append(f"# 🌟 ROS Frontier-Tech Scout — Week of {week_of}")
    md_lines.append("")
    md_lines.append(f"**Roster:** {summary.get('rosterSize', '?')} companies tracked  ·  "
                    f"**Screened this cycle:** {summary.get('candidatesScreened', '?')}  ·  "
                    f"**Top picks:** {len(picks)}  ·  **Runners-up:** {len(runners)}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    if not picks:
        md_lines.append("## ⏸ Quiet week")
        md_lines.append("")
        md_lines.append("The scout screened the full queue but didn't surface any candidates above the threshold (score ≥ 25/70). Either source feeds were quiet or signal density was low. Below: runners-up + raw podcast feed for manual scanning.")
        md_lines.append("")
    else:
        md_lines.append(f"## ⭐ Top {len(picks)} Picks This Week")
        md_lines.append("")
        for i, p in enumerate(picks, 1):
            d = p.get("dimensions", {})
            md_lines.append(f"### {i}. {p['name']}  ·  *Score {int(p.get('score', 0))}/70*")
            md_lines.append("")
            sector = p.get("suggestedSector") or "Frontier Tech"
            md_lines.append(f"**Sector:** {sector}")
            md_lines.append("")
            md_lines.append(f"**Dimensions:** Capital {int(d.get('capital_quality', 0))}, "
                            f"Magnitude {int(d.get('magnitude', 0))}, "
                            f"Tech Depth {int(d.get('tech_depth', 0))}, "
                            f"Frontier Fit {int(d.get('frontier_fit', 0))}, "
                            f"Stealth {int(d.get('stealth_signal', 0))}")
            md_lines.append("")
            brief = p.get("briefing", "").strip()
            if brief:
                md_lines.append(brief)
                md_lines.append("")

            # Verification links
            verify_links = []
            for sig in p.get("signals", [])[:3]:
                url = sig.get("verifyUrl")
                src = sig.get("source", "source")
                if url:
                    verify_links.append(f"[{src}]({url})")
            if verify_links:
                md_lines.append(f"**Verify:** {' · '.join(verify_links)}")
                md_lines.append("")
            md_lines.append("---")
            md_lines.append("")

    if runners:
        md_lines.append(f"## 📋 Runners-up ({len(runners)})")
        md_lines.append("")
        md_lines.append("Worth a quick scan — surfaced in scout but didn't quite make the top 5.")
        md_lines.append("")
        for r in runners[:10]:
            sources = " · ".join(r.get("sources", []))
            sector = r.get("suggestedSector") or "—"
            md_lines.append(f"- **{r['name']}** *({sector})* — {sources} — score {int(r.get('score', 0))}/70")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    if raw_episodes:
        md_lines.append("## 🎧 Raw Podcast Feed (manual scan)")
        md_lines.append("")
        md_lines.append("Recent episodes from the scout's podcast sources. Scan titles for company names the LLM may have missed.")
        md_lines.append("")
        for ep in raw_episodes[:10]:
            podcast = ep.get("podcast", "?")
            title = (ep.get("title") or "")[:120]
            url = ep.get("url", "#")
            md_lines.append(f"- **[{podcast}]** [{title}]({url})")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_lines.append("")
    md_lines.append(f"*Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} · "
                    f"ROS Frontier-Tech Headhunter · "
                    f"30+ VC portfolios + 17 newsletters + 7 podcasts + Form D + DARPA · "
                    f"LLM-extracted via Claude Haiku*")

    md = "\n".join(md_lines)
    OUT_MD.write_text(md)

    # Also emit JSON for downstream email-sender script
    OUT_JSON.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "weekOf": week_of,
        "subject": f"🌟 ROS Frontier-Tech Scout — Week of {week_of} · {len(picks)} picks",
        "markdown": md,
        "topPickNames": [p["name"] for p in picks],
        "summary": summary,
    }, indent=2))

    print(f"✅ Wrote {OUT_MD.relative_to(ROOT)} ({len(md)} chars)")
    print(f"✅ Wrote {OUT_JSON.relative_to(ROOT)} (for email/Slack delivery)")
    print()
    print("Preview:")
    print("=" * 64)
    print(md[:1500])
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
