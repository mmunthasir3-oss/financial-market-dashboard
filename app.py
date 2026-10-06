import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(
    page_title="Financial Market Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Financial Market Analysis & Insight Dashboard")
st.caption("Educational market-analysis dashboard — not financial advice.")


# ==============================
# GET MARKET DATA
# ==============================

@st.cache_data(ttl=900)
def load_data(symbol, period):

    ticker = yf.Ticker(symbol)

    df = ticker.history(
        period=period,
        auto_adjust=False
    )

    if df.empty:
        return pd.DataFrame()

    df = df.reset_index()

    df["Date"] = pd.to_datetime(
        df["Date"]
    ).dt.tz_localize(None)

    return df


# ==============================
# TECHNICAL INDICATORS
# ==============================

def calculate_indicators(df):

    data = df.copy()

    # SMA
    data["SMA20"] = (
        data["Close"]
        .rolling(20)
        .mean()
    )

    data["SMA50"] = (
        data["Close"]
        .rolling(50)
        .mean()
    )

    # EMA
    data["EMA20"] = (
        data["Close"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    # RSI
    delta = data["Close"].diff()

    gain = (
        delta
        .clip(lower=0)
        .rolling(14)
        .mean()
    )

    loss = (
        -delta
        .clip(upper=0)
        .rolling(14)
        .mean()
    )

    rs = gain / loss.replace(0, np.nan)

    data["RSI14"] = (
        100 -
        (100 / (1 + rs))
    )

    # MACD

    ema12 = (
        data["Close"]
        .ewm(
            span=12,
            adjust=False
        )
        .mean()
    )

    ema26 = (
        data["Close"]
        .ewm(
            span=26,
            adjust=False
        )
        .mean()
    )

    data["MACD"] = ema12 - ema26

    data["MACD_Signal"] = (
        data["MACD"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    # Returns

    data["Return_%"] = (
        data["Close"]
        .pct_change()
        * 100
    )

    # Volatility

    data["Volatility_%"] = (
        data["Return_%"]
        .rolling(20)
        .std()
        * np.sqrt(252)
    )

    return data


# ==============================
# INSIGHT ENGINE
# ==============================

def get_insight(df):

    latest = df.iloc[-1]

    score = 0

    reasons = []

    # SMA20

    if pd.notna(latest["SMA20"]):

        if latest["Close"] > latest["SMA20"]:

            score += 1

            reasons.append(
                "Price is above the 20-day SMA."
            )

        else:

            score -= 1

            reasons.append(
                "Price is below the 20-day SMA."
            )

    # SMA50

    if pd.notna(latest["SMA50"]):

        if latest["Close"] > latest["SMA50"]:

            score += 1

            reasons.append(
                "Price is above the 50-day SMA."
            )

        else:

            score -= 1

            reasons.append(
                "Price is below the 50-day SMA."
            )

    # RSI

    if pd.notna(latest["RSI14"]):

        if latest["RSI14"] >= 70:

            reasons.append(
                "RSI suggests an overbought condition."
            )

        elif latest["RSI14"] <= 30:

            reasons.append(
                "RSI suggests an oversold condition."
            )

        else:

            reasons.append(
                "RSI is in a neutral momentum range."
            )

    # MACD

    if (
        latest["MACD"]
        >
        latest["MACD_Signal"]
    ):

        score += 1

        reasons.append(
            "MACD is above its signal line."
        )

    else:

        score -= 1

        reasons.append(
            "MACD is below its signal line."
        )

    # Final trend

    if score >= 2:

        trend = "BULLISH"

    elif score <= -2:

        trend = "BEARISH"

    else:

        trend = "NEUTRAL"

    return trend, reasons


# ==============================
# SIDEBAR INPUT
# ==============================

st.sidebar.header("⚙️ Inputs")

symbol = st.sidebar.text_input(
    "Stock Symbol",
    "RELIANCE.NS"
).strip().upper()

period = st.sidebar.selectbox(
    "Analysis Period",
    [
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y"
    ],
    index=3
)

analyze = st.sidebar.button(
    "🔍 ANALYZE",
    use_container_width=True
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
Examples:

RELIANCE.NS

TCS.NS

INFY.NS

HDFCBANK.NS

AAPL

TSLA
"""
)


# ==============================
# LOAD DATA
# ==============================

if (
    analyze
    or
    "df" not in st.session_state
):

    with st.spinner(
        "Fetching market data..."
    ):

        raw = load_data(
            symbol,
            period
        )

    if raw.empty:

        st.error(
            "Data kidaikkala. "
            "Stock symbol correct-ah enter pannunga."
        )

        st.stop()

    st.session_state["df"] = (
        calculate_indicators(raw)
    )

    st.session_state["symbol"] = symbol


df = st.session_state["df"]

symbol = st.session_state["symbol"]


# ==============================
# LATEST VALUES
# ==============================

latest = df.iloc[-1]

previous = (
    df.iloc[-2]
    if len(df) > 1
    else latest
)

trend, reasons = get_insight(df)

price = latest["Close"]

change = (
    price -
    previous["Close"]
)

change_pct = (
    change /
    previous["Close"]
) * 100

rsi = latest["RSI14"]

vol = latest["Volatility_%"]


# ==============================
# MARKET OVERVIEW
# ==============================

st.subheader(
    f"📊 {symbol} — Market Overview"
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Current Price",
    f"{price:,.2f}",
    f"{change_pct:+.2f}%"
)

c2.metric(
    "RSI (14)",
    f"{rsi:.2f}"
    if pd.notna(rsi)
    else "N/A"
)

c3.metric(
    "Volatility",
    f"{vol:.2f}%"
    if pd.notna(vol)
    else "N/A"
)

c4.metric(
    "20D SMA",
    f"{latest['SMA20']:,.2f}"
    if pd.notna(
        latest["SMA20"]
    )
    else "N/A"
)

c5.metric(
    "Trend",
    trend
)


# ==============================
# PRICE CHART
# ==============================

st.subheader(
    "📈 Price & Moving Averages"
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["Close"],
        name="Close",
        mode="lines"
    )
)

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["SMA20"],
        name="SMA 20",
        mode="lines"
    )
)

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["SMA50"],
        name="SMA 50",
        mode="lines"
    )
)

fig.update_layout(
    height=500,
    xaxis_title="Date",
    yaxis_title="Price",
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ==============================
# INSIGHTS
# ==============================

left, right = st.columns(2)


with left:

    st.subheader(
        "🧠 Automated Insight"
    )

    if trend == "BULLISH":

        st.success(
            f"Overall trend: **{trend}**"
        )

    elif trend == "BEARISH":

        st.error(
            f"Overall trend: **{trend}**"
        )

    else:

        st.warning(
            f"Overall trend: **{trend}**"
        )

    for reason in reasons:

        st.write(
            "•",
            reason
        )


with right:

    st.subheader(
        "📉 Risk & Performance"
    )

    total_return = (
        (
            df["Close"].iloc[-1]
            /
            df["Close"].iloc[0]
        )
        - 1
    ) * 100

    max_price = df["Close"].max()

    min_price = df["Close"].min()

    risk_df = pd.DataFrame({

        "Metric": [
            "Period Return",
            "Highest Price",
            "Lowest Price",
            "Annualized Volatility"
        ],

        "Value": [

            f"{total_return:+.2f}%",

            f"{max_price:,.2f}",

            f"{min_price:,.2f}",

            (
                f"{vol:.2f}%"
                if pd.notna(vol)
                else "N/A"
            )
        ]
    })

    st.dataframe(
        risk_df,
        hide_index=True,
        use_container_width=True
    )


# ==============================
# RSI
# ==============================

st.subheader(
    "📊 RSI Momentum"
)

rsi_fig = go.Figure()

rsi_fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["RSI14"],
        name="RSI 14",
        mode="lines"
    )
)

rsi_fig.add_hline(
    y=70,
    line_dash="dash",
    annotation_text="Overbought 70"
)

rsi_fig.add_hline(
    y=30,
    line_dash="dash",
    annotation_text="Oversold 30"
)

rsi_fig.update_layout(
    height=350,
    yaxis=dict(
        range=[0, 100]
    ),
    xaxis_title="Date",
    yaxis_title="RSI"
)

st.plotly_chart(
    rsi_fig,
    use_container_width=True
)


# ==============================
# MACD
# ==============================

st.subheader(
    "📉 MACD"
)

macd_fig = go.Figure()

macd_fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["MACD"],
        name="MACD",
        mode="lines"
    )
)

macd_fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["MACD_Signal"],
        name="Signal",
        mode="lines"
    )
)

macd_fig.update_layout(
    height=350,
    xaxis_title="Date",
    yaxis_title="MACD"
)

st.plotly_chart(
    macd_fig,
    use_container_width=True
)


# ==============================
# RAW DATA
# ==============================

with st.expander(
    "🗃️ View Raw Market Data"
):

    st.dataframe(
        df.tail(100),
        use_container_width=True
    )


st.caption(
    "Data source: Yahoo Finance via yfinance. "
    "Educational project only."
)