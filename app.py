"""
Income Strategy — institutional performance dashboard (Streamlit).

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

st.set_page_config(page_title="Income Strategy — Performance", layout="wide",
                   initial_sidebar_state="collapsed")

# ---- institutional dark theme -----------------------------------------------
st.markdown("""
<style>
.stApp { background:#0b0e14; color:#e6e9ef; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:1.6rem; max-width:1300px; }
h1,h2,h3,h4 { color:#f4f6fa; font-family:'Inter',-apple-system,sans-serif; letter-spacing:-.01em; }
.kpi { background:#141925; border:1px solid #222a3a; border-radius:12px; padding:18px 20px; }
.kpi .lab { color:#8b93a7; font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; }
.kpi .val { color:#f4f6fa; font-size:1.7rem; font-weight:650; margin-top:4px; }
.kpi .sub { font-size:.8rem; margin-top:2px; }
.pos { color:#3ddc97; } .neg { color:#ff6b6b; } .mut { color:#8b93a7; }
.banner { background:#2a1d0a; border:1px solid #6b4e16; color:#f0c674; border-radius:10px;
          padding:10px 16px; font-size:.86rem; margin-bottom:18px; }
.sect { color:#8b93a7; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em;
        margin:26px 0 8px; border-bottom:1px solid #222a3a; padding-bottom:6px; }
</style>""", unsafe_allow_html=True)

DATA = os.path.join(os.path.dirname(__file__), "data", "snapshot.json")
try:
    snap = json.load(open(DATA))
except Exception:
    st.error("No snapshot found. Run autoagent/dashboard_data.py to generate it.")
    st.stop()

acc = snap.get("account", {})
bt = snap.get("backtest", {})


def pct(x, dp=1): return f"{x*100:+.{dp}f}%"
def cls(x): return "pos" if x >= 0 else "neg"


def kpi(col, label, value, sub="", sub_cls="mut"):
    col.markdown(f"""<div class='kpi'><div class='lab'>{label}</div>
    <div class='val'>{value}</div><div class='sub {sub_cls}'>{sub}</div></div>""",
                 unsafe_allow_html=True)


# ---- header ------------------------------------------------------------------
st.markdown("# Income Strategy")
st.markdown(f"<span class='mut'>Covered-call + gold diversified income · "
            f"updated {snap.get('generated_at','')[:16].replace('T',' ')}</span>",
            unsafe_allow_html=True)
st.markdown(f"<div class='banner'>⚠ <b>{snap.get('status','')}</b> — figures are paper-traded "
            f"and/or backtested. No real capital has achieved these results. Not an offer or "
            f"investment advice. Hypothetical performance has inherent limitations.</div>",
            unsafe_allow_html=True)

# ---- live KPIs ---------------------------------------------------------------
st.markdown("<div class='sect'>Live paper account</div>", unsafe_allow_html=True)
c = st.columns(5)
ret = acc.get("total_return", 0); dd = acc.get("drawdown", 0)
kpi(c[0], "Equity", f"${acc.get('equity',0):,.0f}", f"inception ${acc.get('inception_equity',0):,.0f}")
kpi(c[1], "Return since inception", pct(ret), f"day {acc.get('days_live',0)} · lumpy, judge over months", cls(ret))
kpi(c[2], "Drawdown", pct(-abs(dd)), f"{acc.get('dd_budget_used',0)*100:.0f}% of 20% budget", cls(-dd))
kpi(c[3], "Premium captured", f"${acc.get('net_premium_captured',0):,.0f}", "net option credit, inception-to-date", "pos")
kpi(c[4], "Cash", f"${acc.get('cash',0):,.0f}", "settles into GLD sleeve")

# ---- equity curve ------------------------------------------------------------
curve = acc.get("equity_curve", [])
if curve:
    df = pd.DataFrame(curve); df["date"] = pd.to_datetime(df["date"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["equity"], mode="lines",
                             line=dict(color="#3ddc97", width=2), fill="tozeroy",
                             fillcolor="rgba(61,220,151,0.06)", name="Equity"))
    base = acc.get("inception_equity")
    if base:
        fig.add_hline(y=base, line_dash="dot", line_color="#8b93a7",
                      annotation_text="inception", annotation_font_color="#8b93a7")
    rng = df["equity"].max() - df["equity"].min()
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#8b93a7", showlegend=False,
                      yaxis=dict(gridcolor="#1b2230",
                                 range=[df["equity"].min()-rng*0.3, df["equity"].max()+rng*0.3]),
                      xaxis=dict(gridcolor="#1b2230"))
    st.plotly_chart(fig, use_container_width=True)

# ---- backtested profile ------------------------------------------------------
st.markdown("<div class='sect'>Backtested profile · 2007–2026 (hypothetical)</div>", unsafe_allow_html=True)
c = st.columns(4)
kpi(c[0], "CAGR", pct(bt.get("cagr",0),1), f"vs QQQ {pct(bt.get('bench_cagr',0),1)}", "pos")
kpi(c[1], "Sharpe", f"{bt.get('sharpe',0):.2f}", f"vs QQQ {bt.get('bench_sharpe',0):.2f}", "pos")
kpi(c[2], "Max drawdown", pct(bt.get("max_dd",0),1), f"vs QQQ {pct(bt.get('bench_dd',0),1)} (≈half)", "pos")
kpi(c[3], "Skewness", f"{bt.get('skew',0):.2f}", f"vs QQQ {bt.get('bench_skew',0):.2f} · fatter left tail", "neg")
st.markdown(f"<span class='mut' style='font-size:.8rem'>Pricing: {bt.get('pricing','')}. "
            f"Parameters walk-forward-stable ({snap.get('walkforward',{}).get('verdict','')}). "
            f"Not a tradeable P&L; estimates risk/return shape.</span>", unsafe_allow_html=True)

# ---- regime + benchmark ------------------------------------------------------
left, right = st.columns(2)
with left:
    st.markdown("<div class='sect'>Return by market regime (monthly)</div>", unsafe_allow_html=True)
    rg = pd.DataFrame(snap.get("regime", []))
    if not rg.empty:
        rg["QQQ"] = rg["qqq"].map(lambda x: pct(x)); rg["Strategy"] = rg["strategy"].map(lambda x: pct(x))
        st.dataframe(rg[["regime","months","QQQ","Strategy","note"]].rename(
            columns={"regime":"Regime","months":"# mo","note":""}),
            hide_index=True, use_container_width=True)
    st.markdown("<span class='mut' style='font-size:.78rem'>Profitable in flat markets; "
                "beats buy-&-hold in flat/down/mild; capped in melt-ups; still loses in crashes "
                "(income cushions, does not protect).</span>", unsafe_allow_html=True)
with right:
    st.markdown("<div class='sect'>Vs alternatives (mind the caveat)</div>", unsafe_allow_html=True)
    bm = pd.DataFrame(snap.get("benchmarks", []))
    if not bm.empty:
        bm["CAGR"] = bm["cagr"].map(lambda x: pct(x)); bm["Sharpe"] = bm["sharpe"].map(lambda x: f"{x:.2f}")
        bm["Max DD"] = bm["max_dd"].map(lambda x: pct(x))
        st.dataframe(bm[["name","CAGR","Sharpe","Max DD"]].rename(columns={"name":""}),
                     hide_index=True, use_container_width=True)
    st.markdown("<span class='mut' style='font-size:.78rem'>Strategy is gross/paper/monthly; "
                "ETFs are net-of-fee, real fills, short histories (JEPQ '22+, QQQI '24+). "
                "Shows design soundness, not a demonstrated live edge.</span>", unsafe_allow_html=True)

# ---- gate --------------------------------------------------------------------
g = snap.get("gate", {})
st.markdown("<div class='sect'>Validation status</div>", unsafe_allow_html=True)
st.markdown(f"<span class='mut'>30-day operational gate · day {g.get('day','?')} of {g.get('of',30)} "
            f"({g.get('window','')}). {g.get('purpose','')}</span>", unsafe_allow_html=True)
