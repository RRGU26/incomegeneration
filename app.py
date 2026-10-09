"""
Diversified Trend v1 — performance dashboard (Streamlit). Replaced the covered-call
"Income Strategy" page on 2026-10-09 when the account switched strategies.

Reads dashboard/data/snapshot.json (refreshed daily by autoagent/dashboard_data.py).
Shows live paper-account performance + the backtested research, with prominent
hypothetical/paper labeling. Methodology and the white paper are intentionally NOT here.

Run locally:  streamlit run dashboard/app.py
Deploy:       push repo to GitHub -> share.streamlit.io -> point at dashboard/app.py
"""
import json, os
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Diversified Trend v1 — Performance", layout="wide",
                   initial_sidebar_state="collapsed")

# ---- institutional dark theme -----------------------------------------------
st.markdown("""
<style>
.stApp { background:#0b0e14; color:#e6e9ef; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:1.6rem; max-width:1300px; }
h1,h2,h3,h4 { color:#f4f6fa; font-family:'Inter',-apple-system,sans-serif; letter-spacing:-.01em; }
.kpi { background:#141925; border:1px solid #222a3a; border-radius:12px; padding:16px 18px;
       height:124px; box-sizing:border-box; display:flex; flex-direction:column;
       justify-content:center; overflow:hidden; }
.kpi .lab { color:#8b93a7; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.kpi .val { color:#f4f6fa; font-size:1.65rem; font-weight:650; margin-top:6px; line-height:1.1; }
.kpi .sub { font-size:.78rem; margin-top:6px; line-height:1.2; }
.pos { color:#3ddc97; } .neg { color:#ff6b6b; } .mut { color:#8b93a7; }
.banner { background:#2a1d0a; border:1px solid #6b4e16; color:#f0c674; border-radius:10px;
          padding:10px 16px; font-size:.86rem; margin-bottom:18px; }
.sect { color:#8b93a7; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em;
        margin:26px 0 8px; border-bottom:1px solid #222a3a; padding-bottom:6px; }
.tbl { width:100%; border-collapse:collapse; font-size:.86rem; margin-top:4px; }
.tbl th { text-align:left; color:#8b93a7; font-weight:600; font-size:.68rem; text-transform:uppercase;
          letter-spacing:.05em; padding:9px 12px; border-bottom:1px solid #2a3346; }
.tbl td { padding:10px 12px; border-bottom:1px solid #171d29; color:#d7dbe4; }
.tbl tr:last-child td { border-bottom:none; }
.tbl .num { text-align:right; font-variant-numeric:tabular-nums; }
.tbl tbody tr:hover td { background:#10151f; }
.tbl .hl td { background:#10202e; font-weight:600; color:#f4f6fa; }
.tbl .nm { color:#cfd4de; }
</style>""", unsafe_allow_html=True)

DATA = os.path.join(os.path.dirname(__file__), "data", "snapshot.json")
try:
    snap = json.load(open(DATA))
except Exception:
    st.error("No snapshot found. Run autoagent/dashboard_data.py to generate it.")
    st.stop()

acc = snap.get("account", {})
strat = snap.get("strategy", {})
hist = snap.get("history", {})


def pct(x, dp=1): return f"{x*100:+.{dp}f}%"
def cls(x): return "pos" if x >= 0 else "neg"


def kpi(col, label, value, sub="", sub_cls="mut"):
    col.markdown(f"""<div class='kpi'><div class='lab'>{label}</div>
    <div class='val'>{value}</div><div class='sub {sub_cls}'>{sub}</div></div>""",
                 unsafe_allow_html=True)


# ---- header ------------------------------------------------------------------
st.markdown("# Diversified Trend v1")
st.markdown(f"<span class='mut'>Seven-fund diversified allocation with managed futures · monthly "
            f"rebalance · no options · updated {snap.get('generated_at','')[:16].replace('T',' ')}</span>",
            unsafe_allow_html=True)
st.markdown(f"<div class='banner'>⚠ <b>{snap.get('status','')}</b> — figures are paper-traded "
            f"and/or historical. No real capital has achieved these results. Not an offer or "
            f"investment advice. Past and hypothetical performance have inherent limitations.</div>",
            unsafe_allow_html=True)

def signed(x): return f"<span class='{cls(x)}'>{pct(x)}</span>"

# ---- live account ------------------------------------------------------------
st.markdown("<div class='sect'>Live paper account</div>", unsafe_allow_html=True)
if not acc.get("started"):
    st.info("Diversified Trend v1 has not started yet. The first live run switches the account "
            "from the retired covered-call strategy; results count from that date.")
c = st.columns(5)
kpi(c[0], "Account value", f"${acc.get('equity',0):,.0f}",
    f"start ${acc.get('start_equity',0):,.0f} · {acc.get('start_date') or 'pending'}")
if acc.get("started"):
    r = acc.get("total_return", 0); dd = acc.get("drawdown", 0)
    kpi(c[1], "Earnings since start", f"${acc.get('earnings',0):+,.0f}",
        f"{pct(r)} · excludes contributions", cls(r))
    lines = strat.get("alerts", {})
    nxt = next((v for v in sorted(lines.values()) if dd < v), None)
    kpi(c[2], "Drawdown from peak", pct(-abs(dd)),
        f"next review line {nxt*100:.0f}%" if nxt else "past all review lines — human review", cls(-dd))
    ctl = snap.get("control")
    if ctl:
        kpi(c[3], "Vs control", pct(r - ctl["total_return"]),
            f"control {pct(ctl['total_return'])} (BIL for DBMF/KMLM)", cls(r - ctl["total_return"]))
    else:
        kpi(c[3], "Vs control", "—", "starts after the first refresh")
    vc = acc.get("virtual_contributions", {})
    kpi(c[4], "Virtual contributions", f"${vc.get('total',0):,.0f}",
        f"{vc.get('count',0)} month-ends · not in the account")

# ---- holdings vs target ------------------------------------------------------
st.markdown("<div class='sect'>Holdings vs target</div>", unsafe_allow_html=True)
W = strat.get("weights", {})
held = {p["symbol"]: p for p in acc.get("positions", [])}
rows = "".join(
    f"<tr><td class='nm'>{s_}</td><td class='num'>{W[s_]*100:.0f}%</td>"
    f"<td class='num'>{held.get(s_, {}).get('weight', 0)*100:.1f}%</td>"
    f"<td class='num'>${held.get(s_, {}).get('market_value', 0):,.0f}</td></tr>"
    for s_ in sorted(W, key=lambda k: -W[k]))
other = [p for p in acc.get("positions", []) if p["symbol"] not in W]
rows += "".join(f"<tr><td class='nm mut'>{p['symbol']} (outside allocation)</td><td class='num'>—</td>"
                f"<td class='num'>{p['weight']*100:.1f}%</td><td class='num'>${p['market_value']:,.0f}</td></tr>"
                for p in other)
st.markdown(f"<table class='tbl'><thead><tr><th>Fund</th><th class='num'>Target</th>"
            f"<th class='num'>Actual</th><th class='num'>Value</th></tr></thead><tbody>{rows}</tbody></table>",
            unsafe_allow_html=True)
st.markdown(f"<span class='mut' style='font-size:.8rem'>Rebalanced on the first trading session of "
            f"each month; last: {acc.get('last_rebalance_month') or '—'}. Execution: "
            f"{strat.get('execution','')}.</span>", unsafe_allow_html=True)

# ---- equity curve ------------------------------------------------------------
curve = acc.get("equity_curve", [])
if curve:
    df = pd.DataFrame(curve); df["date"] = pd.to_datetime(df["date"])
    st.markdown("<div class='sect'>Daily account value since start (paper)</div>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["equity"], mode="lines", name="Trend v1",
                             line=dict(color="#3ddc97", width=2.2),
                             hovertemplate="%{x|%b %d}<br>$%{y:,.0f}<extra></extra>"))
    ctl = snap.get("control", {})
    if ctl.get("curve"):
        cdf = pd.DataFrame(ctl["curve"]); cdf["date"] = pd.to_datetime(cdf["date"])
        fig.add_trace(go.Scatter(x=cdf["date"], y=cdf["nav"], mode="lines", name="Control (virtual)",
                                 line=dict(color="#8b93a7", width=1.6, dash="dot"),
                                 hovertemplate="%{x|%b %d}<br>$%{y:,.0f}<extra></extra>"))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#8b93a7", legend=dict(orientation="h"),
                      yaxis=dict(gridcolor="#1b2230"), xaxis=dict(gridcolor="#1b2230"))
    st.plotly_chart(fig, use_container_width=True)

# ---- historical comparison ---------------------------------------------------
st.markdown("<div class='sect'>Historical comparison (real fund prices, pre-tax)</div>", unsafe_allow_html=True)
rows = "".join(
    f"<tr class='{'hl' if i == 0 else ''}'><td class='nm'>{r_['name']}</td>"
    f"<td class='num'>{signed(r_['cagr'])}</td><td class='num'>{signed(r_['max_dd'])}</td>"
    f"<td class='num'>{signed(r_['worst_year'])}</td><td class='num'>{signed(r_['cagr_2025_26'])}</td>"
    f"<td class='num'>{signed(r_['dd_2025_26'])}</td></tr>"
    for i, r_ in enumerate(hist.get("rows", [])))
st.markdown(f"<table class='tbl'><thead><tr><th>Book</th><th class='num'>CAGR</th>"
            f"<th class='num'>Max DD</th><th class='num'>Worst year</th>"
            f"<th class='num'>CAGR 2025-26</th><th class='num'>Max DD 2025-26</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>", unsafe_allow_html=True)
yrs = hist.get("years", {})
if yrs:
    cols = list(next(iter(yrs.values())).keys())
    rows = "".join(f"<tr><td class='nm'>{n}</td>" + "".join(
        f"<td class='num'>{signed(v[c_])}</td>" for c_ in cols) + "</tr>" for n, v in yrs.items())
    st.markdown(f"<table class='tbl'><thead><tr><th>Calendar year</th>" + "".join(
        f"<th class='num'>{c_}</th>" for c_ in cols) + f"</tr></thead><tbody>{rows}</tbody></table>",
        unsafe_allow_html=True)
st.markdown(f"<span class='mut' style='font-size:.8rem'>{hist.get('period','')}. Selected using "
            f"2022-2024; only 2025 onward is out-of-sample.</span>", unsafe_allow_html=True)

# ---- disclosures + deviations ------------------------------------------------
st.markdown("<div class='sect'>Disclosures</div>", unsafe_allow_html=True)
for d_ in snap.get("disclosures", []):
    st.warning(d_)
st.markdown("<div class='sect'>Deviations from the written test protocol</div>", unsafe_allow_html=True)
for d_ in snap.get("deviations", []):
    st.markdown(f"<span class='mut' style='font-size:.85rem'>• {d_}</span>", unsafe_allow_html=True)
