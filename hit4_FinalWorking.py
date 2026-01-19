import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, date
import plotly.graph_objects as go

from dhan_auth import get_dhan_headers

# =================================================
# CONFIG
# =================================================
CSV_FILE_PATH = r"\api-scrip-master-detailed redefined1.csv"

HISTORICAL_URL = "https://api.dhan.co/v2/charts/historical"
INTRADAY_URL   = "https://api.dhan.co/v2/charts/intraday"

HEADERS = get_dhan_headers()

SEGMENT_MAP = {
    "Spot": ("NSE_EQ", "EQUITY"),
    "Current": ("NSE_FNO", "FUTSTK"),
    "Next": ("NSE_FNO", "FUTSTK"),
}

INTERVAL_MAP = {
    "1 min": "1",
    "5 min": "5",
    "15 min": "15",
    "30 min": "30",
    "60 min": "60",
}

DIFF_MODES = {
    "Spot & Current": ("Spot", "Current"),
    "Spot & Next": ("Spot", "Next"),
    "Current & Next": ("Current", "Next"),
}

TRADE_MODES = [
    "B(Current)/Sell(Next)",
    "B(Next)/Sell(Current)"
]

# =================================================
# PAGE
# =================================================
st.set_page_config(layout="wide")
st.title("📊 Dhan OHLC – Main + Difference (Mode Aware)")

# =================================================
# LOAD CSV
# =================================================
@st.cache_data
def load_csv():
    df = pd.read_csv(CSV_FILE_PATH)
    df["Symbols"] = df["Symbols"].str.strip()
    return df

df_master = load_csv()
symbols = sorted(df_master["Symbols"].unique())

# =================================================
# SESSION STATE
# =================================================
if "charts" not in st.session_state:
    st.session_state.charts = []

# =================================================
# ADD CHART BLOCK
# =================================================
if st.button("➕ Add Chart"):
    st.session_state.charts.append({
        "symbol": symbols[0],
        "main_inst": "Spot",
        "interval": "60 min",
        "from": date(2024, 9, 11),
        "to": date(2024, 9, 11),
        "show_diff": False,
        "diff_mode": "Spot & Current",
        "trade_mode": TRADE_MODES[0],
        "main": None,
        "diff": {},
    })

# =================================================
# FETCH FUNCTION (UNCHANGED)
# =================================================
def fetch_ohlc(security_id, inst_key, interval_label, from_dt, to_dt):
    seg, inst = SEGMENT_MAP[inst_key]
    headers = HEADERS.copy()
    same_day = from_dt == to_dt

    if same_day:
        endpoint = INTRADAY_URL
        payload = {
            "securityId": int(security_id),
            "exchangeSegment": seg,
            "instrument": inst,
            "interval": INTERVAL_MAP.get(interval_label, "60"),
            "fromDate": f"{from_dt} 09:15:00",
            "toDate": f"{to_dt} 15:30:00",
            "oi": False
        }
    else:
        endpoint = HISTORICAL_URL
        payload = {
            "securityId": int(security_id),
            "exchangeSegment": seg,
            "instrument": inst,
            "fromDate": str(from_dt),
            "toDate": str(to_dt),
            "oi": False
        }

    r = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    resp = r.json()

    if r.status_code != 200 or "errorCode" in resp:
        return None, endpoint, headers, payload, resp

    df = pd.DataFrame({
        "Time": [datetime.fromtimestamp(t) for t in resp["timestamp"]],
        "Open": resp["open"],
        "High": resp["high"],
        "Low": resp["low"],
        "Close": resp["close"],
    }).set_index("Time")

    return df, endpoint, headers, payload, resp

# =================================================
# DIFFERENCE CALCULATION (MODE-AWARE)
# =================================================
def compute_diff(df_spot, df_cur, df_next, pair, trade_mode, pct=True):

    if pair == "Spot & Current":
        raw = df_cur - df_spot
        return 100 * raw / df_spot if pct else raw

    if pair == "Spot & Next":
        raw = df_next - df_spot
        return 100 * raw / df_spot if pct else raw

    if pair == "Current & Next":
        if trade_mode == "B(Current)/Sell(Next)":
            raw = df_next - df_cur
        else:  # B(Next)/Sell(Current)
            raw = df_cur - df_next

        return 100 * raw / df_cur if pct else raw

# =================================================
# RENDER BLOCKS
# =================================================
for i, c in enumerate(st.session_state.charts):

    st.markdown("---")
    st.subheader(f"Chart Block {i+1}")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    c["symbol"] = col1.selectbox("Symbol", symbols, key=f"s_{i}")
    c["main_inst"] = col2.selectbox("Instrument", ["Spot","Current","Next"], key=f"inst_{i}")
    c["interval"] = col3.selectbox("Interval (intraday)", list(INTERVAL_MAP.keys()), key=f"int_{i}")
    c["from"] = col4.date_input("From", c["from"], key=f"f_{i}")
    c["to"] = col5.date_input("To", c["to"], key=f"t_{i}")

    c["trade_mode"] = col6.selectbox(
        "Mode",
        TRADE_MODES,
        index=TRADE_MODES.index(c["trade_mode"]),
        key=f"mode_{i}"
    )

    c["show_diff"] = st.checkbox("Show Difference Chart", value=c["show_diff"], key=f"sd_{i}")
    if c["show_diff"]:
        c["diff_mode"] = st.selectbox(
            "Difference Pair",
            list(DIFF_MODES.keys()),
            index=list(DIFF_MODES.keys()).index(c["diff_mode"]),
            key=f"dm_{i}"
        )

    # ---------------- DONE ----------------
    if st.button("Done", key=f"d_{i}"):

        c["main"] = None
        c["diff"] = {}

        row = df_master[df_master["Symbols"] == c["symbol"]].iloc[0]

        # ---- MAIN FETCH ----
        df, ep, hdr, req, resp = fetch_ohlc(
            row[c["main_inst"]],
            c["main_inst"],
            c["interval"],
            c["from"],
            c["to"],
        )

        c["main"] = {
            "df": df,
            "endpoint": ep,
            "headers": hdr,
            "request": req,
            "response": resp
        }

        # ---- DIFFERENCE FETCH ----
        if c["show_diff"]:
            for leg in {"Spot", "Current", "Next"}:
                df_leg, ep, hdr, req, resp = fetch_ohlc(
                    row[leg],
                    leg,
                    c["interval"],
                    c["from"],
                    c["to"],
                )
                c["diff"][leg] = {
                    "df": df_leg,
                    "endpoint": ep,
                    "headers": hdr,
                    "request": req,
                    "response": resp
                }

    # ================= MAIN CHART =================
    if c["main"] and c["main"]["df"] is not None:
        df = c["main"]["df"]
        fig = go.Figure()
        for col in ["Open","High","Low","Close"]:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col))
        fig.update_layout(height=380)
        st.plotly_chart(fig, key=f"main_{i}", use_container_width=True)

        with st.expander("📌 Main – Headers / Request / Response / Data"):
            st.json({
                "endpoint": c["main"]["endpoint"],
                "headers": c["main"]["headers"],
                "request": c["main"]["request"],
                "response": c["main"]["response"],
            })
            st.dataframe(df)

    # ================= DIFFERENCE =================
    if c["show_diff"] and all(k in c["diff"] for k in ["Spot","Current","Next"]):

        df_spot = c["diff"]["Spot"]["df"]
        df_cur  = c["diff"]["Current"]["df"]
        df_next = c["diff"]["Next"]["df"]

        if df_spot is not None and df_cur is not None and df_next is not None:

            diff_pct = compute_diff(df_spot, df_cur, df_next, c["diff_mode"], c["trade_mode"], pct=True)
            diff_raw = compute_diff(df_spot, df_cur, df_next, c["diff_mode"], c["trade_mode"], pct=False)

            for title, data in [("Difference (%)", diff_pct), ("Raw Difference", diff_raw)]:
                fig = go.Figure()
                for col in data.columns:
                    fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col))
                fig.update_layout(height=320, yaxis_title=title)
                st.plotly_chart(fig, key=f"{title}_{i}", use_container_width=True)
                st.dataframe(data)

            with st.expander("📌 Difference – Headers / Request / Response"):
                st.json(c["diff"])

