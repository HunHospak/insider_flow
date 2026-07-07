"""Generate a ready-to-post social snippet from the latest feed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    feed = json.loads((ROOT / "out" / "insider_flow.json").read_text(encoding="utf-8"))
    d = feed["data"]
    lines = [f"Insider flow — {d.get('as_of')}"]
    acc = d.get("accumulating", [])[:5]
    if acc:
        lines.append("Insiders accumulating:")
        for x in acc:
            lines.append(f"  {x['ticker']}  score {x['score']:+.2f}  ({x['buys']}B/{x['sells']}S)")
    else:
        lines.append("No open-market insider buying in the window.")
    lines.append("Form 4 data · not investment advice · arkenlabs.eu")
    text = "\n".join(lines)
    (ROOT / "out" / "post.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
