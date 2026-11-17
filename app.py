"""Market Prices & Volatility Lab — The Mountain Path Academy.
Historical prices for stocks, indices, commodities and currencies (Yahoo Finance), return statistics,
historical/EWMA volatility and ARCH/GARCH-family models with forecasts.
"""
import datetime as dt
import io
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

GOLD, BLUE, MID, CARD = "#FFD700", "#003366", "#004d80", "#112240"
TXT, MUTED, GRN, RED, LB = "#e6f1ff", "#8892b0", "#28a745", "#dc3545", "#ADD8E6"
BG = "linear-gradient(135deg,#1a2332,#243447,#2a3f5f)"
SITE = "https://themountainpathacademy.com"
UA = {"User-Agent": "Mozilla/5.0 (education; themountainpathacademy.com)"}
PALETTE = [GOLD, LB, GRN, "#ff9f43", "#c084fc", RED, "#4dd0e1", "#f472b6", "#a3e635", "#fbbf24"]

st.set_page_config(page_title="Market Prices & Volatility Lab | Mountain Path", page_icon="🌊", layout="wide")
st.html(f"""<style>
.stApp{{background:{BG};}}
header[data-testid="stHeader"]{{background:transparent;}}
section[data-testid="stSidebar"]{{background:{CARD};border-right:1px solid {MID};}}
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"]{{
  background:#0b1a33!important;border:1px solid {MID}!important;}}
div[data-baseweb="input"] *, div[data-baseweb="base-input"], div[data-baseweb="select"] > div *,
div[data-testid="stTextInputRootElement"], div[data-testid="stNumberInputContainer"]{{background:#0b1a33!important;}}
input, textarea{{background:#0b1a33!important;color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;caret-color:{GOLD};}}
input::placeholder{{color:{MUTED}!important;-webkit-text-fill-color:{MUTED}!important;opacity:1}}
div[data-baseweb="select"] *{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;}}
div[data-baseweb="select"] svg{{fill:{LB}!important;}}
span[data-tag], span[data-baseweb="tag"]{{background-color:{MID}!important;border:1px solid {GOLD}!important;}}
span[data-tag], span[data-tag] *, span[data-baseweb="tag"] *{{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:700}}
ul[role="listbox"]{{background:{CARD}!important;}}
ul[role="listbox"] li{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;}}
ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"]{{background:{MID}!important;}}
button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"]{{background:{MID}!important;color:{TXT}!important;}}
label, label p, div[data-testid="stWidgetLabel"] p{{color:{LB}!important;-webkit-text-fill-color:{LB}!important;font-weight:600}}
div[data-testid="stCaptionContainer"] p{{color:{MUTED}!important;-webkit-text-fill-color:{MUTED}!important}}
h1,h2,h3,h4{{color:{TXT}!important}}
div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li{{color:{TXT};}}
[role="tab"], [role="tab"] *{{color:{LB}!important;-webkit-text-fill-color:{LB}!important;font-weight:600}}
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] *{{color:{GOLD}!important;-webkit-text-fill-color:{GOLD}!important}}
div[data-baseweb="tab-highlight"]{{background:{GOLD}!important}}
button[data-testid="stBaseButton-primary"], button[kind="primary"]{{background:{GOLD}!important;border:1px solid {GOLD}!important;}}
button[data-testid="stBaseButton-primary"] *, button[kind="primary"] *{{color:{BLUE}!important;-webkit-text-fill-color:{BLUE}!important;font-weight:800}}
button[data-testid="stBaseButton-secondary"], button[kind="secondary"]{{background:{MID}!important;border:1px solid {GOLD}!important;}}
button[data-testid="stBaseButton-secondary"] *, button[kind="secondary"] *{{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:700}}
div[data-testid="stAlert"]{{background:{CARD}!important;border:1px solid {GOLD}!important;}}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] div{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;}}
details summary p{{color:{GOLD}!important;-webkit-text-fill-color:{GOLD}!important;font-weight:700}}
div[data-testid="stExpander"] details{{background:{CARD};border:1px solid {MID};}}
div[role="radiogroup"] p{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important}}
div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"], div[data-testid="stThumbValue"]{{color:{GOLD}!important}}
</style>""")


# ---------------- helpers ----------------
def t(text, color=TXT, size=15, weight=400, extra=""):
    return (f'<span style="color:{color};-webkit-text-fill-color:{color};font-size:{size}px;'
            f'font-weight:{weight};{extra}">{text}</span>')


def card(inner, border=MID, pad="14px 18px"):
    return (f'<div style="background:{CARD};border:1px solid {border};border-radius:12px;padding:{pad};'
            f'user-select:none;-webkit-user-select:none;height:100%">{inner}</div>')


def kpis(items):
    cols = st.columns(len(items))
    for c_, (h, v, s) in zip(cols, items):
        c_.html(card(t(h.upper(), GOLD, 11, 800, "letter-spacing:1px") + "<br>" + t(v, TXT, 22, 800) + "<br>" + t(s, MUTED, 12)))


def explain(title, rows, note=None):
    """Teaching box: formula, worked example with the latest numbers, how to read it."""
    body = ""
    for label, formula, example, read in rows:
        body += (f'<div style="border-left:4px solid {GOLD};padding:10px 14px;margin:0 0 14px;background:rgba(0,51,102,.35);border-radius:6px">'
                 + t(label, GOLD, 15, 800) + "<br>"
                 + t(formula, TXT, 16, 700, "font-family:Georgia,serif") + "<br>"
                 + (t("Example: " + example, LB, 14) + "<br>" if example else "")
                 + t(read, TXT, 14) + "</div>")
    if note:
        body += t(note, MUTED, 13)
    with st.expander(f"📘 {title}"):
        st.html(card(body))


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _stamp6(key):
    return dt.datetime.now(IST)


def provenance(source, freq, latest, retrieved, note=None):
    lat = latest if isinstance(latest, str) else (latest.strftime("%d %b %Y") if latest is not None else "–")
    txt = (f"<b>Source:</b> {source} &nbsp;·&nbsp; <b>Frequency:</b> {freq} &nbsp;·&nbsp; <b>Latest observation:</b> {lat}"
           f" &nbsp;·&nbsp; <b>Retrieved:</b> {retrieved.strftime('%d %b %Y, %H:%M IST')}")
    if note:
        txt += f" &nbsp;·&nbsp; {note}"
    st.html(f'<div style="border-left:3px solid {GOLD};background:rgba(17,34,64,.7);padding:7px 12px;margin:6px 0 10px;'
            f'border-radius:6px;user-select:none;-webkit-user-select:none">{t(txt, LB, 13)}</div>')


def fig_base(title, h=420):
    f = go.Figure()
    f.update_layout(title=dict(text=title, font=dict(color=TXT)), paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(17,34,64,.6)", font=dict(color=TXT), height=h,
                    legend=dict(orientation="h", y=-0.18, font=dict(color=TXT)), margin=dict(l=20, r=20, t=50, b=20),
                    hovermode="x unified")
    f.update_xaxes(gridcolor="rgba(255,255,255,.08)")
    f.update_yaxes(gridcolor="rgba(255,255,255,.08)")
    return f


def register(name, series, unit, source):
    """Keep every loaded series so the Analysis tab can use it."""
    if series is None or len(series.dropna()) == 0:
        return
    st.session_state.setdefault("datasets", {})[name] = {"s": series.dropna().astype(float), "unit": unit, "source": source}


def resample(df, freq, how="last"):
    if freq == "Daily":
        return df
    rule = {"Weekly": "W-FRI", "Monthly": "ME", "Quarterly": "QE", "Annual": "YE"}[freq]
    r = df.resample(rule)
    return (r.last() if how == "last" else r.mean()).dropna(how="all")


def downloads(df, name, key):
    a, b = st.columns(2)
    a.download_button("Download CSV", df.to_csv().encode(), f"{name}.csv", "text/csv", key=f"csv_{key}", width="stretch")
    b.download_button("Download Excel", to_excel({name[:31]: df}), f"{name}.xlsx",
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xl_{key}", width="stretch")


def to_excel(sheets, notes=None):
    from openpyxl.styles import Font, PatternFill, Alignment
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], startrow=3)
            ws = xw.sheets[name[:31]]
            ws["A1"] = name; ws["A1"].font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
            ws["A2"] = f"The Mountain Path Academy · {SITE} · downloaded {dt.date.today().isoformat()}" + (f" · {notes}" if notes else "")
            ws["A2"].font = Font(name="Arial", size=9, italic=True, color="5A6B85")
            for c_ in range(1, len(df.columns) + 2):
                ws.cell(1, c_).fill = PatternFill("solid", fgColor="003366")
                h = ws.cell(4, c_); h.font = Font(name="Arial", bold=True, color="FFFFFF")
                h.fill = PatternFill("solid", fgColor="003366"); h.alignment = Alignment(horizontal="center", wrap_text=True)
                ws.column_dimensions[ws.cell(4, c_).column_letter].width = 14 if c_ > 1 else 13
            for row in ws.iter_rows(min_row=5, min_col=2):
                for c_ in row:
                    if isinstance(c_.value, float):
                        c_.number_format = "#,##0.00"
            for row in ws.iter_rows(min_row=5, max_col=1):
                for c_ in row:
                    c_.number_format = "yyyy-mm-dd"
            ws.freeze_panes = "B5"
    return buf.getvalue()



# ---------------- universe ----------------
UNIVERSE = {
    "Indian indices": {"Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT",
                       "Nifty Next 50": "^NSMIDCP", "Nifty 500": "^CRSLDX", "Nifty Auto": "^CNXAUTO",
                       "Nifty Pharma": "^CNXPHARMA", "Nifty FMCG": "^CNXFMCG", "Nifty Metal": "^CNXMETAL",
                       "India VIX": "^INDIAVIX"},
    "Global indices": {"S&P 500": "^GSPC", "Nasdaq Composite": "^IXIC", "Dow Jones": "^DJI", "FTSE 100": "^FTSE",
                       "DAX": "^GDAXI", "Nikkei 225": "^N225", "Hang Seng": "^HSI", "Shanghai Composite": "000001.SS",
                       "CBOE VIX": "^VIX"},
    "Commodities": {"Gold (US$/oz)": "GC=F", "Silver (US$/oz)": "SI=F", "Crude oil WTI (US$/bbl)": "CL=F",
                    "Brent crude (US$/bbl)": "BZ=F", "Natural gas (US$/MMBtu)": "NG=F", "Copper (US$/lb)": "HG=F",
                    "Platinum (US$/oz)": "PL=F", "Gold (₹ per 10 g, derived)": "DERIVED_GOLD_INR",
                    "Silver (₹ per kg, derived)": "DERIVED_SILVER_INR", "Gold ETF India (GOLDBEES)": "GOLDBEES.NS",
                    "Silver ETF India (SILVERBEES)": "SILVERBEES.NS"},
    "Currencies": {"USD/INR": "USDINR=X", "EUR/INR": "EURINR=X", "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X",
                   "USD/JPY": "USDJPY=X", "US Dollar Index (DXY)": "DX-Y.NYB"},
    "Crypto": {"Bitcoin (US$)": "BTC-USD", "Ether (US$)": "ETH-USD"},
}
LABEL_OF = {v: k for g in UNIVERSE.values() for k, v in g.items()}
OZ = 31.1035  # grams per troy ounce


def ann_factor(sym):
    return 365 if sym.endswith("-USD") else 252


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def yahoo_ohlc(symbol, period):
    """Daily OHLCV from Yahoo Finance with retries; an empty reply raises so it is not cached."""
    import time
    import yfinance as yf
    h = None
    for i_ in range(3):
        try:
            h = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
            if h is not None and not h.empty:
                break
        except Exception:
            pass
        time.sleep(1.5 * (i_ + 1))
    if h is None or h.empty:
        raise RuntimeError(f"No data for {symbol}")
    h.index = pd.to_datetime(h.index).tz_localize(None).normalize()
    h = h[~h.index.duplicated(keep="last")]
    return h[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def load_asset(sym, period):
    if sym == "DERIVED_GOLD_INR" or sym == "DERIVED_SILVER_INR":
        metal = yahoo_ohlc("GC=F" if sym == "DERIVED_GOLD_INR" else "SI=F", period)
        fx = yahoo_ohlc("USDINR=X", period)["Close"]
        mult = 10 / OZ if sym == "DERIVED_GOLD_INR" else 1000 / OZ
        fx = fx.reindex(metal.index).ffill()
        out = metal[["Open", "High", "Low", "Close"]].mul(fx, axis=0) * mult
        out["Volume"] = metal["Volume"]
        return out.dropna(subset=["Close"])
    return yahoo_ohlc(sym, period)


def log_returns(close):
    return (np.log(close / close.shift(1)) * 100).dropna()  # in %


# ---------------- loss-tail risk helpers ----------------
def tail_risk(mean_pct, sigma_pct, confidence, distribution="Normal", nu=None):
    """One-period VaR and ES in log-return percentage loss units; untruncated."""
    from scipy.stats import norm, t as student_t
    if not 0 < confidence < 1 or not np.isfinite(sigma_pct) or sigma_pct < 0:
        raise ValueError("Confidence must be between 0 and 1 and volatility nonnegative.")
    alpha = 1 - confidence
    if distribution == "Student t":
        if nu is None or not np.isfinite(nu) or nu <= 2:
            raise ValueError("Standardised Student t requires degrees of freedom above 2.")
        scale = np.sqrt((nu - 2) / nu)
        tq = student_t.ppf(alpha, nu)
        q = scale * tq
        tail_mean = -scale * (nu + tq * tq) / (nu - 1) * student_t.pdf(tq, nu) / alpha
    else:
        q = norm.ppf(alpha)
        tail_mean = -norm.pdf(q) / alpha
    return -(mean_pct + sigma_pct * q), -(mean_pct + sigma_pct * tail_mean)


def empirical_tail_risk(returns_pct, confidence):
    """Empirical inverse-CDF VaR and exact worst-tail ES with fractional boundary mass."""
    losses = np.sort(-np.asarray(returns_pct, dtype=float))
    losses = losses[np.isfinite(losses)]
    if len(losses) < 2 or not 0 < confidence < 1:
        raise ValueError("At least two finite observations and valid confidence are required.")
    var = float(losses[max(0, int(np.ceil(confidence * len(losses))) - 1)])
    worst = losses[::-1]
    mass = (1 - confidence) * len(worst)
    n = int(np.floor(mass)); fraction = mass - n
    es = (worst[:n].sum() + (fraction * worst[n] if n < len(worst) else 0)) / mass
    return var, float(es)


# ---------------- header ----------------
st.html(card(t("FREE DATA LAB · MBA · CFA · FRM", BLUE, 12, 800,
               f"background:{GOLD};-webkit-text-fill-color:{BLUE};padding:4px 10px;border-radius:5px;letter-spacing:1px") +
             "<br><br>" + t("Market Prices & Volatility Lab", TXT, 34, 800) + "<br>" +
             t("Historical prices for stocks, Indian and global indices, gold, silver, crude oil and currencies. "
               "Measure returns and volatility, then fit and forecast ARCH and GARCH models.", LB, 16), pad="22px 26px"))

# ---------------- sidebar: choose and load ----------------
with st.sidebar:
    st.html(card(t("THE MOUNTAIN PATH ACADEMY", GOLD, 12, 800, "letter-spacing:1.5px") + "<br>" +
                 t("Market Prices & Volatility Lab", TXT, 18, 700)))
    picks = []
    defaults = {"Indian indices": ["Nifty 50", "Nifty Bank"], "Commodities": ["Gold (US$/oz)", "Silver (US$/oz)"],
                "Global indices": ["S&P 500"], "Currencies": ["USD/INR"]}
    for grp, items in UNIVERSE.items():
        sel = st.multiselect(grp, list(items), defaults.get(grp, []), key=f"u_{grp}")
        picks += [items[s] for s in sel]
    custom = st.text_input("Stocks or other Yahoo tickers", placeholder="e.g. RELIANCE.NS, HDFCBANK.NS, AAPL",
                           help="NSE: add .NS · BSE: add .BO · US stocks: plain ticker")
    picks += [c.strip().upper() for c in custom.split(",") if c.strip()]
    period = st.selectbox("History", ["1y", "2y", "5y", "10y", "max"], index=2)
    go_btn = st.button("Load prices", type="primary", width="stretch")
    st.caption("Source: Yahoo Finance (prices adjusted for splits and dividends), kept for 6 hours. "
               "Derived ₹ gold/silver = US$ futures price × USD/INR ÷ 31.1035 g/oz; excludes import duty and GST, "
               "so it sits below MCX and retail prices.")

if go_btn:
    data, bad = {}, []
    with st.spinner("Downloading prices…"):
        for sym in dict.fromkeys(picks):
            try:
                data[sym] = load_asset(sym, period)
            except Exception:
                bad.append(sym)
    st.session_state["px"], st.session_state["px_bad"] = data, bad

PX = st.session_state.get("px", {})
if st.session_state.get("px_bad"):
    st.warning(f"Not loaded: {', '.join(st.session_state['px_bad'])}. Check the ticker or retry in a minute.")


def name(sym):
    return LABEL_OF.get(sym, sym)


if not PX:
    st.html(card(t("How to start", GOLD, 16, 700) + "<br>" +
                 t("1. Pick indices, commodities, currencies or type stock tickers in the sidebar.<br>"
                   "2. Choose the history length and click <b>Load prices</b>.<br>"
                   "3. Explore prices, returns, volatility and GARCH models in the tabs; download any table as CSV or Excel.", TXT, 15)))
else:
    names = {name(s): s for s in PX}
    CLOSE = pd.DataFrame({name(s): PX[s]["Close"] for s in PX})
    tabs = st.tabs(["📈 Prices", "📊 Returns & tests", "🌊 Volatility", "🧮 ARCH / GARCH lab", "🔗 Correlation", "🛡️ VaR & Expected Shortfall"])

    # ---------------- prices ----------------
    with tabs[0]:
        rows = []
        for nm, sym in names.items():
            c = PX[sym]["Close"].dropna()
            def chg(days):
                past = c[c.index <= c.index[-1] - pd.Timedelta(days=days)]
                return c.iloc[-1] / past.iloc[-1] - 1 if len(past) else np.nan
            rows.append({"Asset": nm, "Ticker": sym if not sym.startswith("DERIVED") else "derived", "Last": c.iloc[-1],
                         "Date": c.index[-1].date(), "1 day": c.iloc[-1] / c.iloc[-2] - 1 if len(c) > 1 else np.nan,
                         "1 month": chg(30), "1 year": chg(365),
                         "Volatility 1y (ann.)": log_returns(c[c.index >= c.index[-1] - pd.Timedelta(days=365)]).std() / 100 * np.sqrt(ann_factor(sym))})
        tb = pd.DataFrame(rows).set_index("Asset")
        provenance("Yahoo Finance (closing prices, adjusted for splits and dividends)", "daily closes",
                   max(PX[s_]["Close"].index[-1] for s_ in PX), _stamp6("px|" + "|".join(PX) + period),
                   "latest dates differ by market (see the Date column); prices may be delayed — not a real-time feed")
        st.dataframe(tb.style.format({"Last": "{:,.2f}", "1 day": "{:+.2%}", "1 month": "{:+.2%}", "1 year": "{:+.2%}",
                                      "Volatility 1y (ann.)": "{:.1%}"}, na_rep="–"), width="stretch")
        a, b = st.columns([1, 3])
        view = a.radio("Chart", ["Growth of 100", "Price (one asset)"], key="pv")
        freq = a.selectbox("Frequency", ["Daily", "Weekly", "Monthly"], key="pf")
        if view == "Growth of 100":
            cl = resample(CLOSE.ffill(), freq).dropna(how="all")
            f = fig_base("Growth of 100 (each series rebased to 100 at its first date)", 460)
            for i_, c_ in enumerate(cl.columns):
                s_ = cl[c_].dropna()
                f.add_scatter(x=s_.index, y=s_ / s_.iloc[0] * 100, name=c_, line=dict(color=PALETTE[i_ % 10], width=2))
        else:
            one = a.selectbox("Asset", list(names), key="pone")
            d_ = PX[names[one]]
            if freq != "Daily":
                rule = {"Weekly": "W-FRI", "Monthly": "ME"}[freq]
                d_ = d_.resample(rule).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
            f = fig_base(f"{one} ({freq.lower()})", 460)
            f.add_candlestick(x=d_.index, open=d_["Open"], high=d_["High"], low=d_["Low"], close=d_["Close"], name=one,
                              increasing_line_color=GRN, decreasing_line_color=RED)
            f.update_layout(xaxis_rangeslider_visible=False)
        b.plotly_chart(f, width="stretch")
        out = resample(CLOSE, freq) if freq != "Daily" else CLOSE
        sheets = {"Close prices": out}
        for nm, sym in names.items():
            sheets[re.sub(r"[\[\]:*?/\\]", "", nm)[:31]] = PX[sym]
        a, b = st.columns(2)
        a.download_button("Download closing prices (CSV)", out.to_csv().encode(), f"MPA_prices_{freq}.csv", "text/csv", width="stretch")
        b.download_button("Download all OHLCV (Excel, one sheet per asset)", to_excel(sheets), f"MPA_prices_OHLCV.xlsx",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        st.caption("Assets trade on different calendars (Indian vs US holidays, crypto every day), so rows can have gaps; "
                   "the Excel file keeps each asset's own dates.")

    # ---------------- returns & tests ----------------
    with tabs[1]:
        a, b = st.columns([2, 1])
        nm = a.selectbox("Asset", list(names), key="r_asset")
        rfreq = b.selectbox("Return frequency", ["Daily", "Weekly", "Monthly"], key="r_freq")
        sym = names[nm]
        cl = PX[sym]["Close"]
        if rfreq != "Daily":
            cl = cl.resample({"Weekly": "W-FRI", "Monthly": "ME"}[rfreq]).last().dropna()
        r = log_returns(cl)
        k = {"Daily": ann_factor(sym), "Weekly": 52, "Monthly": 12}[rfreq]
        from scipy import stats as sps
        jb = sps.jarque_bera(r)
        provenance("Yahoo Finance closing prices → log returns", rfreq.lower(), r.index[-1], _stamp6("px|" + "|".join(PX) + period))
        kpis([("Observations", f"{len(r)}", f"{r.index[0].date()} → {r.index[-1].date()}"),
              ("Mean return (ann.)", f"{r.mean() * k:.2f}%", f"{r.mean():.3f}% per period"),
              ("Volatility (ann.)", f"{r.std() * np.sqrt(k):.2f}%", f"{r.std():.3f}% per period"),
              ("Skewness", f"{sps.skew(r):.2f}", "0 for a normal distribution"),
              ("Excess kurtosis", f"{sps.kurtosis(r):.2f}", "0 for normal; > 0 = fat tails")])
        a, b = st.columns(2)
        f = fig_base(f"{nm}: {rfreq.lower()} log returns (%)", 360)
        f.add_scatter(x=r.index, y=r.values, mode="lines", line=dict(color=LB, width=1), name="Return")
        a.plotly_chart(f, width="stretch")
        f = fig_base("Distribution vs normal", 360)
        f.add_histogram(x=r.values, nbinsx=80, histnorm="probability density", marker_color=MID, name="Returns")
        xs = np.linspace(r.min(), r.max(), 200)
        f.add_scatter(x=xs, y=sps.norm.pdf(xs, r.mean(), r.std()), line=dict(color=GOLD, width=3), name="Normal, same mean & sd")
        b.plotly_chart(f, width="stretch")
        from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
        lags = 10
        lb_r = acorr_ljungbox(r, lags=[lags], return_df=True).iloc[0]
        lb_r2 = acorr_ljungbox(r ** 2, lags=[lags], return_df=True).iloc[0]
        lm = het_arch(r - r.mean(), nlags=lags)
        a, b = st.columns(2)
        f = fig_base("Autocorrelation: returns vs squared returns", 320)
        L = list(range(1, 21))
        f.add_bar(x=L, y=[r.autocorr(l_) for l_ in L], name="Returns", marker_color=LB)
        f.add_bar(x=L, y=[(r ** 2).autocorr(l_) for l_ in L], name="Squared returns", marker_color=GOLD)
        f.add_hline(y=1.96 / np.sqrt(len(r)), line=dict(color=RED, dash="dot"))
        f.add_hline(y=-1.96 / np.sqrt(len(r)), line=dict(color=RED, dash="dot"))
        f.update_layout(barmode="group"); f.update_xaxes(title="Lag")
        a.plotly_chart(f, width="stretch")
        tests = pd.DataFrame({
            "Statistic": [jb.statistic, lb_r["lb_stat"], lb_r2["lb_stat"], lm[0]],
            "p-value": [jb.pvalue, lb_r["lb_pvalue"], lb_r2["lb_pvalue"], lm[1]],
            "Null hypothesis": ["Returns are normally distributed", f"No autocorrelation in returns (lags 1–{lags})",
                                f"No autocorrelation in squared returns (lags 1–{lags})", f"No ARCH effects (lags 1–{lags})"]},
            index=["Jarque-Bera", "Ljung-Box Q (returns)", "Ljung-Box Q (squared returns)", "Engle ARCH-LM"])
        tests["Result at 5%"] = np.where(tests["p-value"] < 0.05, "Reject", "Do not reject")
        b.dataframe(tests.style.format({"Statistic": "{:,.2f}", "p-value": "{:.4f}"}), width="stretch")
        b.caption("If squared returns are autocorrelated and ARCH-LM rejects, volatility clusters: a GARCH model is appropriate.")
        explain("How the returns and tests are calculated", [
            ("Log return", "r<sub>t</sub> = ln(P<sub>t</sub> ÷ P<sub>t−1</sub>) × 100",
             f"latest: ln({cl.iloc[-1]:,.2f} ÷ {cl.iloc[-2]:,.2f}) × 100 = {r.iloc[-1]:+.3f}%",
             "Log returns add up over time, which is why volatility models use them."),
            ("Annualising", f"Annual mean = mean × {k};  annual volatility = sd × √{k}",
             f"{r.std():.3f}% × √{k} = {r.std() * np.sqrt(k):.2f}%",
             "Uses 252 trading days a year (365 for crypto, 52 weeks, 12 months). The √ rule assumes returns are independent."),
            ("Jarque-Bera", "JB = n/6 × [S² + K²/4]   (S = skewness, K = excess kurtosis)",
             f"n = {len(r)}, S = {sps.skew(r):.2f}, K = {sps.kurtosis(r):.2f} → JB = {jb.statistic:,.0f}",
             "Large JB = returns are not normal. Financial returns usually have fat tails (K > 0): extreme days happen far more often than a normal distribution predicts."),
            ("Ljung-Box and ARCH-LM", "Q = n(n+2) Σ ρ̂<sub>k</sub>² ÷ (n−k);  ARCH-LM: regress r²<sub>t</sub> on its own lags, LM = n × R²",
             None, "Returns themselves are usually close to unautocorrelated, but squared returns are strongly autocorrelated: "
                   "big moves follow big moves (volatility clustering). That pattern is exactly what ARCH/GARCH models capture."),
        ])
        rr = pd.DataFrame({"Close": cl, "Log return %": log_returns(cl)})
        downloads(rr, f"Returns_{re.sub('[^A-Za-z0-9]+', '_', nm)}_{rfreq}", "ret")

    # ---------------- volatility ----------------
    with tabs[2]:
        a, b, c = st.columns([2, 1, 1])
        nm = a.selectbox("Asset", list(names), key="v_asset")
        lam = b.number_input("EWMA λ (lambda)", 0.80, 0.995, 0.94, 0.005, format="%.3f",
                             help="RiskMetrics uses 0.94 for daily data.")
        wins = c.multiselect("Rolling windows (days)", [10, 21, 63, 126, 252], [21, 63], key="v_w")
        sym = names[nm]
        k = ann_factor(sym)
        r = log_returns(PX[sym]["Close"])
        V = pd.DataFrame(index=r.index)
        for w in wins:
            V[f"Rolling {w}-day"] = r.rolling(w).std() * np.sqrt(k)
        ew = np.empty(len(r)); ew[0] = r.iloc[:30].var()
        for i_ in range(1, len(r)):
            ew[i_] = lam * ew[i_ - 1] + (1 - lam) * r.iloc[i_ - 1] ** 2
        V[f"EWMA (λ = {lam:.2f})"] = np.sqrt(ew) * np.sqrt(k)
        hl = PX[sym][["High", "Low"]].reindex(r.index)
        park = np.sqrt((np.log(hl["High"] / hl["Low"]) ** 2).rolling(21).mean() / (4 * np.log(2))) * 100 * np.sqrt(k)
        if park.notna().sum() > 30 and (hl["High"] > hl["Low"]).mean() > 0.8:
            V["Parkinson 21-day (high-low)"] = park
        implied = {"^NSEI": ("^INDIAVIX", "India VIX (implied)"), "^GSPC": ("^VIX", "CBOE VIX (implied)")}.get(sym)
        if implied:
            try:
                iv = load_asset(implied[0], period)["Close"].reindex(V.index)
                V[implied[1]] = iv
            except Exception:
                pass
        lastv = V.dropna(how="all").iloc[-1]
        kpis([(c_[:26], f"{lastv[c_]:.1f}%", "annualised, latest") for c_ in V.columns[:5] if pd.notna(lastv[c_])])
        f = fig_base(f"{nm}: annualised volatility (%)", 460)
        for i_, c_ in enumerate(V.columns):
            f.add_scatter(x=V.index, y=V[c_], name=c_, line=dict(color=PALETTE[i_ % 10], width=2 if "implied" not in c_ else 3,
                                                                  dash="dot" if "implied" in c_ else None))
        st.plotly_chart(f, width="stretch")
        explain("How each volatility measure is calculated", [
            ("Rolling (historical) volatility", "σ = standard deviation of the last N daily log returns × √" + str(k),
             None, "Every day in the window gets equal weight, and a shock drops out abruptly N days later (the 'ghost' effect)."),
            ("EWMA (RiskMetrics)", "σ²<sub>t</sub> = λ σ²<sub>t−1</sub> + (1 − λ) r²<sub>t−1</sub>",
             f"λ = {lam:.2f}: yesterday's squared return gets weight {1 - lam:.2f}, and weights decay by λ each day",
             "Reacts quickly to new shocks and fades them smoothly. It is GARCH(1,1) with ω = 0 and α + β = 1, so it has no "
             "long-run mean to revert to."),
            ("Parkinson (high-low)", "σ² = [1 ÷ (4 ln 2)] × average of [ln(High ÷ Low)]²  over 21 days",
             None, "Uses the intraday range, so it is more efficient than close-to-close volatility when high/low prices are reliable."),
            ("Implied volatility (VIX)", "Backed out of option prices: the market's expected volatility over the next 30 days",
             None, "Historical measures look backward; VIX looks forward. Implied volatility is usually above realised "
                   "volatility (the volatility risk premium)."),
        ])
        downloads(V.dropna(how="all"), f"Volatility_{re.sub('[^A-Za-z0-9]+', '_', nm)}", "vol")

    # ---------------- ARCH / GARCH lab ----------------
    with tabs[3]:
        from arch import arch_model
        a, b, c, d = st.columns(4)
        nm = a.selectbox("Asset", list(names), key="g_asset")
        model = b.selectbox("Model", ["GARCH(1,1)", "GJR-GARCH(1,1)", "EGARCH(1,1)", "ARCH(1)"], key="g_model")
        dist = c.selectbox("Error distribution", ["Student t", "Normal"], key="g_dist")
        hor = d.number_input("Forecast horizon (days)", 1, 250, 22, key="g_h")
        a, b = st.columns(2)
        yrs = a.slider("Estimation window (years, most recent)", 1, 20, 5, key="g_yrs")
        meanm = b.radio("Mean equation", ["Constant", "Zero"], horizontal=True, key="g_mean")
        rc1, rc2 = st.columns(2)
        g_conf = rc1.number_input("VaR / ES confidence level (%)", min_value=90.0, max_value=99.9, value=99.0, step=0.5, format="%.1f", key="g_conf") / 100
        g_value = rc2.number_input("Long position value (amount in chosen currency)", min_value=1.0, value=1000000.0, step=10000.0, key="g_position")
        st.caption("Risk horizon: one observation (one trading day for exchange assets, one calendar day for daily crypto). Monetary losses use a linear log-return approximation in the position's own currency; no FX conversion.")
        sym = names[nm]
        k = ann_factor(sym)
        r = log_returns(PX[sym]["Close"])
        r = r[r.index >= r.index[-1] - pd.DateOffset(years=yrs)]
        spec = {"GARCH(1,1)": dict(vol="GARCH", p=1, o=0, q=1), "GJR-GARCH(1,1)": dict(vol="GARCH", p=1, o=1, q=1),
                "EGARCH(1,1)": dict(vol="EGARCH", p=1, o=1, q=1), "ARCH(1)": dict(vol="ARCH", p=1)}
        dname = "t" if dist == "Student t" else "normal"

        @st.cache_data(show_spinner=False)
        def fit(sym_, yrs_, model_, dname_, mean_, n_, last_):
            am = arch_model(r, mean=mean_, dist=dname_, rescale=False, **spec[model_])
            return am.fit(disp="off")

        if len(r) < 250:
            st.warning("At least about one year of daily data is needed; increase the history in the sidebar.")
        else:
            try:
                with st.spinner("Estimating by maximum likelihood…"):
                    res = fit(sym, yrs, model, dname, meanm, len(r), str(r.index[-1]))
            except Exception as e:
                res = None
                st.error(f"Estimation failed: {e}")
            if res is not None:
                P = res.params
                al, be, ga = P.get("alpha[1]", 0.0), P.get("beta[1]", 0.0), P.get("gamma[1]", 0.0)
                om, mu = P.get("omega", np.nan), P.get("mu", 0.0)
                if model == "GARCH(1,1)":
                    pers = al + be
                elif model == "GJR-GARCH(1,1)":
                    pers = al + be + ga / 2
                elif model == "ARCH(1)":
                    pers = al
                else:
                    pers = be
                lr_var = om / (1 - pers) if model != "EGARCH(1,1)" and pers < 1 else None
                lr_vol = np.sqrt(lr_var * k) if lr_var else None
                half = np.log(0.5) / np.log(pers) if 0 < pers < 1 else None
                h_meth = "simulation" if (model == "EGARCH(1,1)" and hor > 1) else "analytic"
                fc = res.forecast(horizon=int(hor), reindex=False, method=h_meth,
                                  **({"simulations": 1000} if h_meth == "simulation" else {}))
                fvar = fc.variance.iloc[-1].values
                cvol = res.conditional_volatility
                s1 = np.sqrt(fvar[0])
                nu = P.get("nu")
                selected_var, selected_es = tail_risk(mu, s1, g_conf, dist, nu)
                risk_rows = []
                for conf in sorted(set([.90, .95, .975, .99, .995, .999, float(g_conf)])):
                    v_, e_ = tail_risk(mu, s1, conf, dist, nu)
                    risk_rows.append({"Confidence %": conf * 100, "1-day VaR loss %": v_, "1-day ES loss %": e_,
                                      "VaR amount (approx.)": g_value * v_ / 100, "ES amount (approx.)": g_value * e_ / 100})
                risk_table = pd.DataFrame(risk_rows).set_index("Confidence %")
                kpis([("Persistence", f"{pers:.4f}", "α + β" if model == "GARCH(1,1)" else ("α + β + γ/2" if "GJR" in model else ("β" if "EGARCH" in model else "α"))),
                      ("Half-life of a shock", f"{half:.1f} days" if half else "–", "ln 0.5 ÷ ln(persistence)"),
                      ("Long-run volatility", f"{lr_vol:.1f}%" if lr_vol else "–", "annualised, √(ω ÷ (1 − persistence) × " + str(k) + ")"),
                      ("Volatility today → tomorrow", f"{cvol.iloc[-1] * np.sqrt(k):.1f}% → {s1 * np.sqrt(k):.1f}%", "annualised"),
                      ("1-day VaR / ES", f"{selected_var:.2f}% / {selected_es:.2f}%", f"{g_conf:.1%} confidence · {dist} errors")])
                st.markdown("#### Conditional 1-day VaR and Expected Shortfall")
                st.dataframe(risk_table.style.format({c: "{:,.3f}" for c in risk_table.columns}), width="stretch")
                st.info(f"At {g_conf:.1%} confidence, model VaR is {selected_var:.3f}%: the model assigns {1-g_conf:.1%} probability to a worse daily log-return loss. ES / CVaR is {selected_es:.3f}%: the average loss within that worst tail. Approximate position amounts are {g_value*selected_var/100:,.2f} and {g_value*selected_es/100:,.2f}, respectively.")
                st.caption("ES (Expected Shortfall) is also called CVaR (Conditional Value at Risk). Here 'conditional' GARCH risk also means the forecast uses information available at the last observation. No square-root-of-time VaR/ES extrapolation is applied to the multi-day volatility chart.")
                pt = pd.DataFrame({"Estimate": P, "Std. error": res.std_err, "t-stat": res.tvalues, "p-value": res.pvalues})
                a, b = st.columns([1, 1])
                with a:
                    st.markdown("**Parameter estimates**")
                    st.dataframe(pt.style.format({"Estimate": "{:.5f}", "Std. error": "{:.5f}", "t-stat": "{:.2f}", "p-value": "{:.4f}"}),
                                 width="stretch")
                    st.caption(f"Log-likelihood {res.loglikelihood:,.1f} · AIC {res.aic:,.1f} · BIC {res.bic:,.1f} · "
                               f"{res.nobs} daily returns, {r.index[0].date()} → {r.index[-1].date()}")
                with b:
                    ft = pd.DataFrame({"Daily variance (%²)": fvar, "Daily vol %": np.sqrt(fvar),
                                       "Annualised vol %": np.sqrt(fvar * k),
                                       "Cumulative vol to day h %": np.sqrt(np.cumsum(fvar))},
                                      index=pd.Index(range(1, int(hor) + 1), name="Day ahead"))
                    f = fig_base("Volatility forecast — out-of-sample (annualised %)", 300)
                    f.add_scatter(x=ft.index, y=ft["Annualised vol %"], name="Forecast (model output)", line=dict(color=GOLD, width=3, dash="dash"))
                    if lr_vol:
                        f.add_hline(y=lr_vol, line=dict(color=LB, dash="dot"), annotation_text="long-run", annotation_font_color=LB)
                    f.update_xaxes(title="Days ahead")
                    st.plotly_chart(f, width="stretch")
                f = fig_base(f"{nm}: fitted (in-sample) {model} volatility vs observed 21-day realised volatility (annualised %)", 400)
                f.add_scatter(x=r.index, y=r.rolling(21).std() * np.sqrt(k), name="Observed: 21-day realised volatility", line=dict(color=LB, width=1))
                f.add_scatter(x=cvol.index, y=cvol * np.sqrt(k), name=f"Fitted (in-sample): {model} σ_t", line=dict(color=GOLD, width=2))
                st.plotly_chart(f, width="stretch")
                st.html(card(t("WHAT IS DATA AND WHAT IS MODEL OUTPUT", GOLD, 11, 800, "letter-spacing:1px") + "<br>" +
                             t(f"<b>Observed:</b> {res.nobs} daily log returns of {nm}, {r.index[0].date()} → {r.index[-1].date()}. "
                               f"<b>Fitted (in-sample):</b> σ<sub>t</sub> estimated by maximum likelihood on those same returns. "
                               f"<b>Forecast (out-of-sample):</b> the next {int(hor)} days. The forecast and the VaR assume the estimated "
                               f"parameters stay constant, no structural break or jump, and {dist.lower()} errors; they are model "
                               f"estimates with their own uncertainty, not observed data. Parameter estimates are as of {r.index[-1].date()}.",
                               TXT, 14), border=GOLD))
                eqs = {
                    "ARCH(1)": "σ²<sub>t</sub> = ω + α ε²<sub>t−1</sub>",
                    "GARCH(1,1)": "σ²<sub>t</sub> = ω + α ε²<sub>t−1</sub> + β σ²<sub>t−1</sub>",
                    "GJR-GARCH(1,1)": "σ²<sub>t</sub> = ω + (α + γ I<sub>t−1</sub>) ε²<sub>t−1</sub> + β σ²<sub>t−1</sub>,  I = 1 if ε<sub>t−1</sub> &lt; 0",
                    "EGARCH(1,1)": "ln σ²<sub>t</sub> = ω + α(|z<sub>t−1</sub>| − E|z|) + γ z<sub>t−1</sub> + β ln σ²<sub>t−1</sub>"}
                worked = None
                if model in ("GARCH(1,1)", "GJR-GARCH(1,1)", "ARCH(1)"):
                    e_last = float(res.resid.iloc[-1]); s_last = float(cvol.iloc[-1])
                    ind = 1 if e_last < 0 else 0
                    nxt = om + (al + ga * ind) * e_last ** 2 + be * s_last ** 2
                    worked = (f"ω {om:.4f} + ({al:.4f}" + (f" + {ga:.4f}×{ind}" if "GJR" in model else "") +
                              f") × ({e_last:+.3f})² " + (f"+ {be:.4f} × {s_last:.3f}² " if model != "ARCH(1)" else "") +
                              f"= {nxt:.4f} → σ = {np.sqrt(nxt):.3f}% daily = {np.sqrt(nxt * k):.1f}% annualised")
                explain(f"How {model} works and how to read the results", [
                    ("Variance equation", eqs[model], worked,
                     "ε<sub>t</sub> = r<sub>t</sub> − μ is the return surprise. ω sets the floor, α is the reaction to yesterday's "
                     "shock, β is the memory of yesterday's variance. Parameters are found by maximising the likelihood of the "
                     "observed returns."),
                    ("Persistence and half-life", "Half-life = ln(0.5) ÷ ln(persistence)",
                     f"persistence {pers:.4f} → {half:.1f} days" if half else None,
                     "Close to 1 = shocks to volatility fade slowly. A half-life of 30 days means half of today's excess volatility "
                     "is still there a month later. EWMA is the special case with persistence exactly 1."),
                    ("Long-run (unconditional) volatility", "σ²<sub>LR</sub> = ω ÷ (1 − persistence)",
                     f"{om:.4f} ÷ (1 − {pers:.4f}) = {lr_var:.4f} %² daily → {lr_vol:.1f}% annualised" if lr_vol else
                     "For EGARCH the level is read from the long-horizon forecast.",
                     "Forecasts converge to this level: up from below in calm markets, down from above after a shock."),
                    ("Leverage effect (GJR, EGARCH)", "γ > 0 in GJR (γ < 0 in EGARCH) = bad news raises volatility more than good news",
                     f"γ = {ga:.4f}" if "GJR" in model or "EGARCH" in model else None,
                     "Typical for equity indices; usually weak or absent for gold and currencies."),
                    ("Student t errors", "ν (nu) = degrees of freedom",
                     f"ν = {nu:.1f}" if nu is not None else None,
                     "Fat tails beyond what volatility clustering explains. ν below about 10 = clearly fat-tailed. "
                     "Compare AIC/BIC with normal errors: lower is better."),
                    ("1-day VaR and Conditional VaR", "VaR = −(μ + σ × q); ES = −(μ + σ × E[z | z ≤ q]), q = F⁻¹(1 − confidence)",
                     f"Confidence {g_conf:.1%}, mean {mu:.3f}%, next-day σ {s1:.3f}% → VaR {selected_var:.3f}%, ES {selected_es:.3f}%",
                     "VaR is the loss threshold; ES / CVaR averages the worse tail. Student t shocks are standardised to unit variance, consistent with the fitted arch model. Monetary values are linear approximations for a long position."),
                ], note="Returns are daily log returns in %, so ω is in %² per day. Estimated with the Python 'arch' package (maximum likelihood).")
                st.markdown("#### Compare models")
                if st.button("Fit all models (GARCH, GJR, EGARCH, ARCH × Normal, Student t)", key="g_all"):
                    rows = []
                    for m_ in spec:
                        for d_ in ["normal", "t"]:
                            try:
                                rs_ = fit(sym, yrs, m_, d_, meanm, len(r), str(r.index[-1]))
                                P_ = rs_.params
                                pe_ = {"GARCH(1,1)": P_.get("alpha[1]", 0) + P_.get("beta[1]", 0),
                                       "GJR-GARCH(1,1)": P_.get("alpha[1]", 0) + P_.get("beta[1]", 0) + P_.get("gamma[1]", 0) / 2,
                                       "EGARCH(1,1)": P_.get("beta[1]", 0), "ARCH(1)": P_.get("alpha[1]", 0)}[m_]
                                rows.append({"Model": m_, "Errors": "Student t" if d_ == "t" else "Normal",
                                             "Log-likelihood": rs_.loglikelihood, "AIC": rs_.aic, "BIC": rs_.bic,
                                             "Persistence": pe_, "Vol today (ann. %)": rs_.conditional_volatility.iloc[-1] * np.sqrt(k)})
                            except Exception:
                                pass
                    cmp_ = pd.DataFrame(rows).sort_values("AIC").reset_index(drop=True)
                    cmp_.index = cmp_.index + 1
                    st.session_state["g_cmp"] = (nm, cmp_)
                if st.session_state.get("g_cmp") and st.session_state["g_cmp"][0] == nm:
                    cmp_ = st.session_state["g_cmp"][1]
                    st.dataframe(cmp_.style.format({"Log-likelihood": "{:,.1f}", "AIC": "{:,.1f}", "BIC": "{:,.1f}",
                                                    "Persistence": "{:.4f}", "Vol today (ann. %)": "{:.1f}"}), width="stretch")
                    st.caption("Ranked by AIC (lower is better). BIC penalises extra parameters more heavily.")
                cv = pd.DataFrame({"Log return %": r, "Conditional vol % (daily)": cvol,
                                   "Conditional vol % (annualised)": cvol * np.sqrt(k), "Standardised residual": res.std_resid})
                xl = to_excel({"Parameters": pt, "Conditional volatility": cv, "Forecast": ft, "VaR and Expected Shortfall": risk_table,
                               "Risk assumptions": pd.DataFrame({"Value": [nm, model, dist, str(nu), str(g_conf), str(g_value), "One observation; daily log-return loss; monetary linear approximation"]}, index=["Asset", "Model", "Distribution", "Student t df", "Confidence", "Position value", "Horizon and units"])})
                a, b = st.columns(2)
                a.download_button("Download model results (Excel)", xl, f"{model}_{re.sub('[^A-Za-z0-9]+', '_', nm)}.xlsx",
                                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
                b.download_button("Download returns for your own GARCH (CSV)", r.rename("log_return_pct").to_csv().encode(),
                                  f"returns_{re.sub('[^A-Za-z0-9]+', '_', nm)}.csv", "text/csv", width="stretch")

    # ---------------- correlation ----------------
    with tabs[4]:
        if CLOSE.shape[1] < 2:
            st.html(card(t("Load at least two assets to see correlations.", TXT, 15)))
        else:
            cfreq = st.radio("Return frequency", ["Daily", "Weekly", "Monthly"], index=1, horizontal=True, key="c_f")
            cl = CLOSE.ffill() if cfreq == "Daily" else resample(CLOSE.ffill(), cfreq)
            R = np.log(cl / cl.shift(1)).dropna(how="any")
            if cfreq == "Daily":
                R = R[(R != 0).all(axis=1)]  # drop days when one market was closed
            C = R.corr()
            f = go.Figure(go.Heatmap(z=C.values, x=C.columns, y=C.index, zmin=-1, zmax=1,
                                     colorscale=[[0, RED], [0.5, "#112240"], [1, GOLD]],
                                     text=np.round(C.values, 2), texttemplate="%{text}", textfont=dict(color=TXT)))
            f.update_layout(title=dict(text=f"Correlation of {cfreq.lower()} log returns ({len(R)} periods)", font=dict(color=TXT)),
                            paper_bgcolor="rgba(0,0,0,0)", font=dict(color=TXT), height=120 + 50 * len(C), margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(f, width="stretch")
            a, b, c = st.columns(3)
            x1 = a.selectbox("Asset 1", list(C.columns), 0, key="c1")
            x2 = b.selectbox("Asset 2", list(C.columns), 1, key="c2")
            w = c.number_input("Rolling window (periods)", 10, 260, 52 if cfreq == "Weekly" else (63 if cfreq == "Daily" else 24), key="cw")
            rc = R[x1].rolling(int(w)).corr(R[x2])
            f = fig_base(f"Rolling {int(w)}-period correlation: {x1} vs {x2}", 320)
            f.add_scatter(x=rc.index, y=rc, line=dict(color=GOLD, width=2), name="Correlation")
            f.add_hline(y=0, line=dict(color=MUTED, dash="dot"))
            st.plotly_chart(f, width="stretch")
            st.caption("Daily returns use only dates on which every selected market traded. Correlations are not stable: "
                       "they often jump towards 1 in crises, just when diversification is needed most.")
            downloads(C, f"Correlation_{cfreq}", "corr")

    # ---------------- standalone historical / normal VaR and ES ----------------
    with tabs[5]:
        st.markdown("### VaR & Conditional VaR (Expected Shortfall)")
        a, b, c = st.columns(3)
        risk_asset = a.selectbox("Risk asset", list(names), key="risk_asset")
        risk_conf = b.number_input("Confidence level (%)", 90.0, 99.9, 99.0, .5, format="%.1f", key="risk_conf") / 100
        risk_value = c.number_input("Long position value (own currency)", 1.0, value=1000000.0, step=10000.0, key="risk_value")
        rr = log_returns(PX[names[risk_asset]]["Close"])
        risk_years = st.slider("Risk estimation window (years)", 1, 20, 5, key="risk_years")
        rr = rr[rr.index >= rr.index[-1] - pd.DateOffset(years=risk_years)]
        if len(rr) < 30:
            st.warning("Load at least 30 daily observations to estimate tail risk.")
        else:
            hvar, hes = empirical_tail_risk(rr, risk_conf)
            nvar, nes = tail_risk(float(rr.mean()), float(rr.std(ddof=1)), risk_conf)
            risk_summary = pd.DataFrame([
                ["Historical simulation", hvar, hes, risk_value*hvar/100, risk_value*hes/100],
                ["Normal (constant volatility)", nvar, nes, risk_value*nvar/100, risk_value*nes/100],
            ], columns=["Method", "1-day VaR loss %", "1-day ES / CVaR loss %", "VaR amount (approx.)", "ES amount (approx.)"]).set_index("Method")
            kpis([("Confidence", f"{risk_conf:.1%}", "one daily observation"),
                  ("Historical VaR", f"{hvar:.3f}%", f"worst-tail probability {1-risk_conf:.1%}"),
                  ("Historical ES / CVaR", f"{hes:.3f}%", "average worst-tail loss"),
                  ("Tail sample size", f"{len(rr)*(1-risk_conf):.1f}", f"effective observations of {len(rr)}")])
            st.dataframe(risk_summary.style.format("{:,.3f}"), width="stretch")
            if len(rr)*(1-risk_conf) < 20:
                st.warning("Fewer than 20 effective tail observations: historical ES is highly sensitive to the sample and confidence level.")
            f = fig_base(f"{risk_asset}: observed daily log-return losses (%)", 400)
            f.add_histogram(x=-rr, nbinsx=60, marker_color=LB, name="Observed losses")
            f.add_vline(x=hvar, line_color=GOLD, line_dash="dash", annotation_text="Historical VaR", annotation_font_color=GOLD)
            f.add_vline(x=hes, line_color=RED, line_dash="dot", annotation_text="Historical ES", annotation_font_color=RED)
            f.update_xaxes(title="Loss in daily log-return % (negative = gain)")
            st.plotly_chart(f, width="stretch")
            st.info("VaR answers: what loss threshold is exceeded with the chosen tail probability? ES / CVaR answers: how large is the average loss in that worst tail? Neither is a maximum possible loss.")
            with st.expander("Formulas, units and assumptions"):
                st.latex(r"VaR_c=-\mu+\sigma\Phi^{-1}(c),\qquad ES_c=-\mu+\sigma\frac{\phi(\Phi^{-1}(c))}{1-c}")
                st.markdown("Normal estimates use the sample daily mean and standard deviation. Historical VaR uses the empirical inverse CDF; historical ES averages exactly the worst (1 − confidence) fraction, with a fractional boundary observation where needed. Estimates can be negative if even the selected tail corresponds to a gain; values are not floored at zero.")
                st.markdown("Returns are log returns in percent. Loss amounts equal position value × loss % ÷ 100: a linear approximation, not exact compounded P&L. Amounts use the position's own currency without FX conversion. One observation means one trading day for exchange assets and one calendar day for daily crypto. These estimates concern a long, linear exposure; options and short positions require separate payoff modelling.")
                st.markdown("Historical and constant-volatility estimates describe the sample. For forward-looking, time-varying risk use the confidence selector and ES table in ARCH / GARCH lab. No multi-day square-root scaling is applied.")
            meta = pd.DataFrame({"Value": [risk_asset, str(risk_conf), str(risk_value), str(len(rr)), str(rr.index[0].date()), str(rr.index[-1].date()), "One observation; daily log-return losses; monetary linear approximation"]}, index=["Asset", "Confidence", "Position value", "Sample size", "Start", "End", "Horizon and units"])
            a, b = st.columns(2)
            a.download_button("Download VaR / ES CSV", risk_summary.to_csv().encode(), "VaR_Expected_Shortfall.csv", "text/csv", key="risk_csv", width="stretch")
            b.download_button("Download VaR / ES Excel", to_excel({"VaR and ES": risk_summary, "Daily log returns": rr.to_frame("Log return %"), "Assumptions": meta}), "VaR_Expected_Shortfall.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="risk_excel", width="stretch")

# ---------------- footer ----------------
st.html(f"""<div style="margin-top:28px;padding:16px 10px;border-top:2px solid {GOLD};text-align:center;user-select:none;-webkit-user-select:none">
{t("The Mountain Path Academy · Prof. V. Ravichandran", TXT, 14, 700)}<br>
<a href="{SITE}" target="_blank" style="color:{GOLD};-webkit-text-fill-color:{GOLD};text-decoration:none;font-weight:700">{SITE}</a>
{t(" · ", MUTED)}<a href="https://www.linkedin.com/in/trichyravis" target="_blank" style="color:{GOLD};-webkit-text-fill-color:{GOLD};text-decoration:none;font-weight:700">LinkedIn</a>
{t(" · ", MUTED)}<a href="https://github.com/trichyravis" target="_blank" style="color:{GOLD};-webkit-text-fill-color:{GOLD};text-decoration:none;font-weight:700">GitHub</a><br>
{t("Data: Yahoo Finance. Education only — not investment advice.", MUTED, 12)}</div>""")

