# Income Strategy — Performance Dashboard

A live, daily-updating performance dashboard for a systematic **covered-call + gold
diversified income** strategy.

🔗 **Live dashboard:** _(deploy on Streamlit Community Cloud — see below)_

---

> ## ⚠️ Important disclosures
> - All figures are **paper-traded and/or backtested. No real capital has achieved
>   these results.** The strategy is in a validation phase and has not traded live money.
> - Multi-year figures are **hypothetical / backtested**, prepared with hindsight, and do
>   not reflect actual trading. Hypothetical performance has inherent limitations.
> - This dashboard is **not an offer**, a solicitation, or investment advice, and is not a
>   recommendation to buy or sell any security. Options involve substantial risk of loss.
> - Past and simulated performance do not predict future results.

---

## What this shows

- **Live paper account** — equity, return since inception, drawdown vs budget, premium collected
- **Backtested profile** (2007–2026, hypothetical) — return, Sharpe, drawdown, skew vs the index
- **Return by market regime** — how the strategy behaves in crashes, flat markets, and rallies
- **Benchmark comparison** — vs the Nasdaq-100 and income ETFs (with caveats noted in-app)

The strategy's *methodology and parameters are intentionally not published here* — this
repository contains only the dashboard application and the performance numbers it displays.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
1. Go to https://share.streamlit.io → **New app**
2. Repository: `RRGU26/incomegeneration`, branch `main`, main file `app.py`
3. Deploy. The app reads `data/snapshot.json`, which is refreshed daily.

No credentials are needed — the app only reads a committed data snapshot.
