import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# पेज की सेटिंग
st.set_page_config(page_title="Darvas Nifty 500 Pro Scanner", page_icon="📈", layout="wide")

st.title("📈 जय श्री राम - Darvas Nifty 500 Pro Scanner (Full Auto)")
st.caption("Nifty 500 के सभी शेयरों का लाइव डार्वस बॉक्स स्कैनर (BUY • HOLD • EXIT)")

# --- साइडबार सेटिंग्स ---
st.sidebar.header("⚙️ ऐप सेटिंग्स")
ntfy_topic = st.sidebar.text_input("मोबाइल अलर्ट कोड (ntfy Topic):", value="darvas_alert_rituraj_108")
capital = st.sidebar.number_input("आपकी कुल पूंजी (₹):", value=100000, step=10000)

# ऑटो-स्कैन मोड
auto_scan = st.sidebar.checkbox("🔄 Auto-Pilot Mode चालू करें (हर 15 मिनट में ऑटो-स्कैन)", value=False)

def send_mobile_notification(title, message):
    try:
        url = f"https://ntfy.sh/{ntfy_topic}"
        headers = {
            "Title": title.encode('utf-8'),
            "Priority": "high",
            "Tags": "chart_with_upwards_trend,bell"
        }
        requests.post(url, data=message.encode('utf-8'), headers=headers, timeout=5)
        return True
    except Exception:
        return False

if st.sidebar.button("🔔 फोन पर टेस्ट अलर्ट भेजें"):
    ok = send_mobile_notification("Darvas Nifty 500 Ready!", "बधाई हो! आपका Nifty 500 स्कैनर आपके फोन से जुड़ गया है।")
    if ok:
        st.sidebar.success("आपके फोन पर अलर्ट भेज दिया गया है!")

def find_true_darvas_box(df):
    highs = df['High'].values
    lows = df['Low'].values
    box_top, box_bottom = None, None

    if len(df) < 35:
        return None, None

    for i in range(len(df) - 30, len(df) - 4):
        if highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]:
            potential_top = highs[i]
            for j in range(i + 1, len(df) - 4):
                if lows[j] < lows[j+1] and lows[j] < lows[j+2] and lows[j] < lows[j+3]:
                    box_top = float(potential_top)
                    box_bottom = float(lows[j])
                    break
    return box_top, box_bottom

def scan_stock(symbol, nifty_return_60d):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period="6mo")
        if df.empty or len(df) < 120:
            return None

        live_price = float(df['Close'].iloc[-1])
        live_volume = float(df['Volume'].iloc[-1])

        ema_50 = float(df['Close'].ewm(span=50, adjust=False).mean().iloc[-1])
        ema_200 = float(df['Close'].ewm(span=200, adjust=False).mean().iloc[-1]) if len(df) >= 200 else ema_50
        high_52w = float(df['High'].max())
        avg_vol_20 = float(df['Volume'].tail(20).iloc[:-1].mean())

        stock_return_60d = (live_price / float(df['Close'].iloc[-60])) - 1 if len(df) >= 60 else 0
        rs_strong = stock_return_60d > nifty_return_60d

        box_top, box_bottom = find_true_darvas_box(df)
        if not box_top or not box_bottom:
            return None

        box_width_pct = ((box_top - box_bottom) / box_bottom) * 100
        vol_ratio = round(live_volume / avg_vol_20, 1) if avg_vol_20 > 0 else 1.0

        stage2_uptrend = (
            live_price > ema_50 and
            live_price >= (high_52w * 0.82) and
            rs_strong and
            box_width_pct <= 18.0
        )

        risk_per_share = max(live_price - box_bottom, 1.0)
        qty = max(int((capital * 0.01) / risk_per_share), 1)

        if live_price > box_top and stage2_uptrend and vol_ratio >= 1.3:
            signal = "BUY"
        elif live_price < box_bottom:
            signal = "EXIT"
        else:
            signal = "HOLD"

        return {
            "Stock": symbol,
            "Signal": signal,
            "Live Price (₹)": round(live_price, 2),
            "Box Top (Breakout)": round(box_top, 2),
            "Box Bottom (SL)": round(box_bottom, 2),
            "Box Width": f"{round(box_width_pct, 1)}%",
            "Volume": f"{vol_ratio}x",
            "Qty (सुझाव)": qty
        }
    except Exception:
        return None

@st.cache_data
def get_nifty_500_symbols():
    return [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "LTIM", "ITC", "KOTAKBANK",
        "LT", "AXISBANK", "HINDUNILVR", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN", "NTPC", "TATAMOTORS",
        "POWERGRID", "ASIANPAINT", "BAJAJFINSV", "NESTLEIND", "M&M", "TATASTEEL", "GRASIM", "HCLTECH", "ADANIENT",
        "ADANIPORTS", "COALINDIA", "BAJAJ-AUTO", "ONGC", "WIPRO", "HDFCLIFE", "SBILIFE", "TECHM", "BRITANNIA",
        "INDUSINDBK", "DIVISLAB", "TATACONSUM", "CIPLA", "APOLLOHOSP", "EICHERMOT", "BPCL", "HEROMOTOCO",
        "HAL", "BEL", "TRENT", "ZOMATO", "JIOFIN", "NAUKRI", "VEDL", "PIDILITIND", "SBICARD", "DLF",
        "SIEMENS", "ABB", "CUMMINSIND", "POLYCAB", "DIXON", "PERSISTENT", "TATAELXSI", "MPHASIS", "COFORGE",
        "MUTHOOTFIN", "CHOLAFIN", "SHRIRAMFIN", "SRF", "AMBUJACEM", "ACC", "SHREECEM", "ICICIGI", "ICICIPRULI"
    ]

stock_symbols = get_nifty_500_symbols()
my_portfolio_input = st.text_input("💼 आपके खरीदे हुए शेयर (कॉमा लगाकर लिखें):", value="HAL, SBIN")

run_scan = st.button("🚀 Nifty स्कैन शुरू करें", use_container_width=True)

if run_scan or auto_scan:
    with st.spinner("शेयरों का डार्वस बॉक्स स्कैन हो रहा है... कृपया कुछ सेकंड प्रतीक्षा करें..."):
        nifty_df = yf.Ticker("^NSEI").history(period="6mo")
        nifty_ret = (float(nifty_df['Close'].iloc[-1]) / float(nifty_df['Close'].iloc[-60])) - 1 if len(nifty_df) >= 60 else 0.0

        my_holdings = [s.strip().upper() for s in my_portfolio_input.split(",") if s.strip()]
        results = []
        
        progress_bar = st.progress(0)
        total_stocks = len(stock_symbols)

        for idx, sym in enumerate(stock_symbols):
            res = scan_stock(sym, nifty_ret)
            if res:
                results.append(res)
                if res["Signal"] == "BUY":
                    send_mobile_notification(
                        f"BUY ALERT: {sym} @ Rs.{res['Live Price (₹)']}",
                        f"Box Top तोड़ा! Stop Loss: Rs.{res['Box Bottom (SL)']} | Qty: {res['Qty (सुझाव)']}"
                    )
                elif res["Signal"] == "EXIT" and sym in my_holdings:
                    send_mobile_notification(
                        f"EXIT ALERT: {sym} से बाहर निकलें!",
                        f"प्राइस Rs.{res['Live Price (₹)']} आपके Box Bottom के नीचे चला गया है!"
                    )
            progress_bar.progress((idx + 1) / total_stocks)

        progress_bar.empty()

        if results:
            res_df = pd.DataFrame(results)
            tab1, tab2, tab3 = st.tabs(["🟢 BUY (खरीदने योग्य)", "🟡 HOLD (होल्ड करें)", "🔴 EXIT (बेच दें)"])

            with tab1:
                buy_df = res_df[res_df["Signal"] == "BUY"]
                if not buy_df.empty:
                    st.success(f"कुल {len(buy_df)} शेयरों में शानदार एडवांस ब्रेकआउट मिला है!")
                    st.dataframe(buy_df, use_container_width=True)
                else:
                    st.info("वर्तमान में किसी शेयर में ब्रेकआउट नहीं है।")

            with tab2:
                hold_df = res_df[res_df["Signal"] == "HOLD"]
                st.dataframe(hold_df, use_container_width=True)

            with tab3:
                exit_df = res_df[res_df["Signal"] == "EXIT"]
                if not exit_df.empty:
                    st.error("सावधान! इन शेयरों ने अपना स्टॉप-लॉस तोड़ दिया है:")
                    st.dataframe(exit_df, use_container_width=True)
                else:
                    st.success("कोई भी शेयर खतरे में नहीं है।")

    if auto_scan:
        time.sleep(900)
        st.rerun()
        
