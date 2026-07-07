"""Pure computation for insider_flow. No I/O, unit-testable.

For each ticker, aggregate open-market insider buys (code 'P') and sales (code 'S') over the
window into a signed flow score in [-1, +1]:
    score = (buy_shares - sell_shares) / (buy_shares + sell_shares)
Positive => insiders net accumulating; negative => net distributing.
Grants (A), option exercises (M) and other codes are ignored — they are not open-market signal.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _aggregate_ticker(txns: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    buy_shares = 0.0
    sell_shares = 0.0
    n_buys = 0
    n_sells = 0
    for t in txns:
        code = t.get("code")
        chg = float(t.get("change") or 0)
        if code == "P" and chg > 0:
            buy_shares += chg
            n_buys += 1
        elif code == "S" and chg < 0:
            sell_shares += -chg
            n_sells += 1
    denom = buy_shares + sell_shares
    if denom <= 0:
        return None
    score = (buy_shares - sell_shares) / denom
    return {
        "score": round(score, 3),
        "net_shares": round(buy_shares - sell_shares),
        "buys": n_buys,
        "sells": n_sells,
    }


def build_boards(per_ticker: Dict[str, List[Dict[str, Any]]], cfg: Dict[str, Any], has_key: bool,
                 as_of: str) -> Dict[str, Any]:
    top_n = int(cfg.get("top_n", 20))
    min_abs = float(cfg.get("min_abs_score", 0.05))

    agg: Dict[str, Dict[str, Any]] = {}
    for tk, txns in per_ticker.items():
        a = _aggregate_ticker(txns or [])
        if a:
            agg[tk] = a

    rows = [dict(ticker=tk, **v) for tk, v in agg.items()]
    accumulating = sorted([r for r in rows if r["score"] >= min_abs], key=lambda r: -r["score"])[:top_n]
    distributing = sorted([r for r in rows if r["score"] <= -min_abs], key=lambda r: r["score"])[:top_n]
    by_ticker = {tk: {"score": v["score"], "net_shares": v["net_shares"]} for tk, v in agg.items()}

    if not has_key:
        status, notes = "unavailable", "No FINNHUB_API_KEY set; insider flow not fetched."
    elif not agg:
        status, notes = "partial", "No open-market insider buys/sells in the window."
    else:
        status, notes = "active", None

    return {
        "as_of": as_of,
        "scanned": len(per_ticker),
        "with_activity": len(agg),
        "accumulating": accumulating,
        "distributing": distributing,
        "by_ticker": by_ticker,
        "_status": status,
        "_notes": notes,
    }
