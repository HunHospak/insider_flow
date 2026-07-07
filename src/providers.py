"""Ingest: Finnhub insider-transactions (Form 4) per ticker over a universe.

Defensive: no key or network failure -> empty payload, and build_feed emits a graceful
status. Rate-limited via config.request_sleep_sec to stay under the free tier.
"""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

_HEADERS = {"User-Agent": "arkenlabs-insider-flow/1.0"}


def load_universe(path: Path, limit: int) -> List[str]:
    out: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip().upper()
        if not s or s.startswith("#"):
            continue
        out.append(s)
        if len(out) >= limit:
            break
    return out


def fetch_insider(ticker: str, api_key: str, base_url: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """Return raw transactions [{code, change, date}] for one ticker. Empty on any error."""
    try:
        r = requests.get(
            f"{base_url.rstrip('/')}/stock/insider-transactions",
            params={"symbol": ticker, "from": from_date, "to": to_date, "token": api_key},
            timeout=10, headers=_HEADERS,
        )
    except Exception:
        return []
    if r.status_code != 200:
        return []
    try:
        data = r.json().get("data") or []
    except Exception:
        return []
    txns: List[Dict[str, Any]] = []
    for it in data:
        try:
            change = float(it.get("change") or 0)
        except (TypeError, ValueError):
            continue
        txns.append({
            "code": str(it.get("transactionCode") or "").upper(),
            "change": change,
            "date": it.get("transactionDate") or it.get("filingDate"),
        })
    return txns


def gather(cfg: Dict[str, Any], api_key: str | None) -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    universe = load_universe(root / cfg["universe_file"], int(cfg.get("max_tickers", 60)))
    if not api_key:
        return {"per_ticker": {}, "universe_size": len(universe), "has_key": False}

    today = dt.date.today()
    from_date = (today - dt.timedelta(days=int(cfg.get("lookback_days", 90)))).isoformat()
    to_date = today.isoformat()
    sleep_s = float(cfg.get("request_sleep_sec", 1.1))
    base_url = cfg.get("base_url", "https://finnhub.io/api/v1")

    per_ticker: Dict[str, List[Dict[str, Any]]] = {}
    for tk in universe:
        per_ticker[tk] = fetch_insider(tk, api_key, base_url, from_date, to_date)
        time.sleep(sleep_s)
    return {"per_ticker": per_ticker, "universe_size": len(universe), "has_key": True}
