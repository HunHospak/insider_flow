# insider_flow

Independent ArkenLabs satellite. Scans a universe of tickers for open-market insider (Form 4)
buys and sells via **Finnhub**, and publishes a net accumulation/distribution feed. Fully
decoupled — the app fetches it read-only and degrades gracefully if offline.

## Produces `out/insider_flow.json`

`data`:
- `accumulating` — insiders net buying: `{ticker, score, net_shares, buys, sells}` (score in [-1, +1])
- `distributing` — insiders net selling
- `by_ticker` — per-symbol map for the company page

Only open-market buys (code `P`) and sales (code `S`) count. Grants and option exercises are ignored.

## Setup (needs a free Finnhub key)

1. Get a key at https://finnhub.io (free tier).
2. Local: `cp .env.example .env` and set `FINNHUB_API_KEY=...`
3. CI: add `FINNHUB_API_KEY` as a repository secret (the workflow already reads it).

Without a key the feed publishes as `status: "unavailable"` and the app panel simply hides.

## Run locally

```bash
pip install -r requirements.txt
python src/build_feed.py && python scripts/post_text.py
```

Universe is `universe.txt` (kept modest to respect Finnhub's free 60 req/min limit).

## Not investment advice

Informational insider-activity data from regulatory filings.
