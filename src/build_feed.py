"""Orchestration: ingest -> compute -> validate(schema) -> write out/."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

from providers import gather  # noqa: E402
from compute import build_boards  # noqa: E402


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def load_schema() -> dict:
    return json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def build(cfg: dict) -> dict:
    api_key = os.environ.get(cfg.get("api_key_env", "")) or None
    raw = gather(cfg, api_key)
    boards = build_boards(raw.get("per_ticker", {}), cfg, raw.get("has_key", False), dt.date.today().isoformat())
    status = boards.pop("_status")
    notes = boards.pop("_notes", None)
    boards["disclaimer"] = "Open-market insider (Form 4) activity. Informational only, not investment advice."

    feed = {
        "service": cfg["service"],
        "schema_version": str(cfg["schema_version"]),
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "ttl_hours": cfg["ttl_hours"],
        "data": boards,
    }
    if notes:
        feed["notes"] = notes
    return feed


def main() -> None:
    cfg = load_config()
    feed = build(cfg)
    jsonschema.validate(feed, load_schema())
    out = ROOT / "out"
    (out / "history").mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2)
    (out / "insider_flow.json").write_text(payload, encoding="utf-8")
    (out / "history" / f"{feed['data']['as_of']}.json").write_text(payload, encoding="utf-8")
    print(f"[insider_flow] status={feed['status']} with_activity={feed['data']['with_activity']}/{feed['data']['scanned']}")


if __name__ == "__main__":
    main()
