import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# पेज की सेटिंग (मोबाइल स्क्रीन के हिसाब से)
st.set_page_config(page_title="Darvas Pro Scanner", page_icon="📈", layout="centered")

st.title("📈 जय श्री राम - Darvas Pro App")
st.caption("लाइव एडवांस डार्वस बॉक्स स्कैनर (BUY • HOLD • EXIT)")

# --- साइडबार सेटिंग्स (नोटिफिकेशन और कैपिटल) ---
st.sidebar.header("⚙️ ऐप सेटिंग्स")
ntfy_topic = st.sidebar.text_input("मोबाइल अलर्ट कोड (ntfy Topic):", value="darvas_alert_rituraj_108")
capital = st.sidebar.number_input("आपकी कुल पूंजी (₹):", value=100000, step=10000)

# मोबाइल पर नोटिफिकेशन भेजने का फंक्शन
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

# टेस्ट नोटिफिकेशन बटन
if st.sidebar.button("🔔 फोन पर टेस्ट अलर्ट भेजें"):
    ok = send_mobile_notification("Darvas Pro Ready!", "बधाई हो! आपका डार्वस स्कैनर आपके फोन से जुड़ गया है।")
    if ok:
        st.sidebar.success("आपके फोन पर अलर्ट भेज दिया गया है!")

# --- एडवांस डार्वस बॉक्स का गणित (6 Super Filters) ---
def find_true_darvas_box(df):
    highs = df['High'].values
    lows = df['Low'].values
    box_top, box_bottom = None, None

    if len(df) < 35:
        return None, None

    # पिछले 30 दिनों में 3-Day Pivot के साथ असली बॉक्स ढूँढना
    for i in range(len(df) - 30, len(df) - 4):
        if highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]:
            potential_top = highs[i]
            for j in range(i + 1, len(df) - 4):
                if lows[j] < lows[j+1] and lows[j] < lows[j+2] and lows[j] < lows[j+3]:
                    box_top = float(potential_top)
                    box_bottom = float(lows[j])
                    break
    return box_top, box_bottom

def scan_stock(symbol, nifty_return_60d, my_holdings):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period="1y")
        if df.empty or len(df) < 200:
            return None

        # लाइव/नवीनतम डेटा
        live_price = float(df['Close'].iloc[-1])
        live_volume = float(df['Volume'].iloc[-1])

        # Moving Averages और 52-Week High
        ema_50 = float(df['Close'].ewm(span=50, adjust=False).mean().iloc[-1])
        ema_200 = float(df['Close'].ewm(span=200, adjust=False).mean().iloc[-1])
        high_52w = float(df['High'].tail(250).max())
        avg_vol_20 = float(df['Volume'].tail(20).iloc[:-1].mean())

        # Relative Strength (60 दिन की तुलना)
        stock_return_60d = (live_price / float(df['Close'].iloc[-60])) - 1
        rs_strong = stock_return_60d > nifty_return_60d

        # Darvas Box निकालें
        box_top, box_bottom = find_true_darvas_box(df)
        if not box_top or not box_bottom:
            return None

        box_width_pct = ((box_top - box_bottom) / box_bottom) * 100
        vol_ratio = round(live_volume / avg_vol_20, 1) if avg_vol_20 > 0 else 1.0

        # एडवांस अपट्रेंड फ़िल्टर
        stage2_uptrend = (
            live_price > ema_50 > ema_200 and
            live_price >= (high_52w * 0.85) and
            rs_strong and
            box_width_pct <= 16.0
        )

        # रिस्क के हिसाब से कितनी क्वांटिटी खरीदें (1% रिस्क नियम)
        risk_per_share = max(live_price - box_bottom, 1.0)
        qty = max(int((capital * 0.01) / risk_per_share), 1)

        # सिग्नल तय करना
        if live_price > box_top and stage2_uptrend and vol_ratio >= 1.4:
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
            "Qty (सुझाव)": qty,
            "In Portfolio": symbol in my_holdings
        }
    except Exception:
        return None

# --- यूज़र की वॉचलिस्ट और पोर्टफोलियो ---
default_stocks = "HAL, BEL, TRENT, SBIN, RELIANCE, LT, M&M, SUNPHARMA, BAJFINANCE, TATAELXSI,PERSISTENT, DIXON, POLYCAB, CUMMINSIND, ZOMATO"
stocks_input = st.text_area("📋 स्कैन करने वाले शेयर (NSE नाम):", value=default_stocks)
my_portfolio_input = st.text_input("💼 आपके खरीदे हुए शेयर (जिनको ट्रैक करना है):", value="HAL, SBIN")

if st.button("🚀 अभी लाइव मार्केट स्कैन करें", use_container_width=True):
    with st.spinner("Nifty और शेयरों का डार्वस बॉक्स स्कैन हो रहा है... कृपया 10-15 सेकंड रुकें..."):
        # Nifty 50 का डेटा
        nifty_df = yf.Ticker("^NSEI").history(period="6mo")
        nifty_ret = (float(nifty_df['Close'].iloc[-1]) / float(nifty_df['Close'].iloc[-60])) - 1 if len(nifty_df) >= 60 else 0.0

        stock_list = [s.strip().upper() for s in stocks_input.split(",") if s.strip()]
        my_holdings = [s.strip().upper() for s in my_portfolio_input.split(",") if s.strip()]

        results = []
        for sym in stock_list:
            res = scan_stock(sym, nifty_ret, my_holdings)
            if res:
                results.append(res)
                # अगर BUY या आपके खरीदे हुए शेयर में EXIT आए तो फोन पर घंटी बजाएं
                if res["Signal"] == "BUY":
                    send_mobile_notification(
                        f"BUY ALERT: {sym} @ Rs.{res['Live Price (₹)']}",
                        f"Box Top Rs.{res['Box Top (Breakout)']} टूटा! Stop Loss: Rs.{res['Box Bottom (SL)']} | Volume: {res['Volume']} | Qty: {res['Qty (सुझाव)']}"
                    )
                elif res["Signal"] == "EXIT" and res["In Portfolio"]:
                    send_mobile_notification(
                        f"EXIT ALERT: {sym} से बाहर निकलें!",
                        f"प्राइस (Rs.{res['Live Price (₹)']}) आपके Box Bottom (Rs.{res['Box Bottom (SL)']}) के नीचे चला गया है!"
                    )

        if results:
            res_df = pd.DataFrame(results)
            tab1, tab2, tab3 = st.tabs(["🟢 BUY (एंट्री लें)", "🟡 HOLD (बने रहें)", "🔴 EXIT (निकल जाएं)"])

            with tab1:
                buy_df = res_df[res_df["Signal"] == "BUY"]
                if not buy_df.empty:
                    st.success("इन शेयरों में एडवांस डार्वस ब्रेकआउट हुआ है!")
                    st.dataframe(buy_df, use_container_width=True)
                else:
                    st.info("अभी किसी शेयर में पक्का एडवांस ब्रेकआउट नहीं है।")

            with tab2:
                hold_df = res_df[res_df["Signal"] == "HOLD"]
                st.write("ये शेयर अपने बॉक्स के अंदर सुरक्षित हैं (Trailing SL के साथ होल्ड करें):")
                st.dataframe(hold_df, use_container_width=True)

            with tab3:
                exit_df = res_df[res_df["Signal"] == "EXIT"]
                if not exit_df.empty:
                    st.error("सावधान! इन शेयरों ने अपना Box Bottom (Stop-Loss) तोड़ दिया है:")
                    st.dataframe(exit_df, use_container_width=True)
                else:
                    st.success("कोई भी शेयर खतरे के निशान (Box Bottom) के नीचे नहीं है।")
                    
