import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="Darvas Pro Scanner", page_icon="📈", layout="wide")

st.title("📈 जय श्री राम - Darvas Pro Scanner")
st.caption("लाइटवेट क्रैश-प्रूफ एडिशन (BUY • HOLD • EXIT)")

# साइडबार
st.sidebar.header("⚙️ सेटिंग्स")
ntfy_topic = st.sidebar.text_input("ntfy अलर्ट कोड:", value="darvas_alert_rituraj_108")
capital = st.sidebar.number_input("कुल पूंजी (₹):", value=100000, step=10000)

def send_alert(title, msg):
    try:
        url = f"https://ntfy.sh/{ntfy_topic}"
        headers = {"Title": title.encode('utf-8'), "Priority": "high"}
        requests.post(url, data=msg.encode('utf-8'), headers=headers, timeout=5)
        return True
    except Exception:
        return False

if st.sidebar.button("🔔 टेस्ट अलर्ट भेजें"):
    if send_alert("Darvas Pro Active!", "अलर्ट सिस्टम सही काम कर रहा है।"):
        st.sidebar.success("अलर्ट भेज दिया गया!")

# डार्वस बॉक्स लॉजिक (मेमोरी फ्रेंडली)
def get_darvas_box(df):
    if len(df) < 25:
        return None, None
    highs = df['High'].values
    lows = df['Low'].values
    box_top, box_bottom = None, None

    for i in range(len(df) - 20, len(df) - 4):
        if highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]:
            top = highs[i]
            for j in range(i + 1, len(df) - 4):
                if lows[j] < lows[j+1] and lows[j] < lows[j+2] and lows[j] < lows[j+3]:
                    box_top = float(top)
                    box_bottom = float(lows[j])
                    break
    return box_top, box_bottom

def scan_single(sym):
    try:
        t = yf.Ticker(f"{sym}.NS")
        # सिर्फ 60 दिन का डेटा (ताकि सर्वर 500 एरर न दे)
        df = t.history(period="60d")
        if df.empty or len(df) < 30:
            return None

        live_price = float(df['Close'].iloc[-1])
        live_vol = float(df['Volume'].iloc[-1])
        avg_vol = float(df['Volume'].tail(15).iloc[:-1].mean())
        ema_20 = float(df['Close'].ewm(span=20, adjust=False).mean().iloc[-1])

        box_top, box_bottom = get_darvas_box(df)
        if not box_top or not box_bottom:
            return None

        width = ((box_top - box_bottom) / box_bottom) * 100
        vol_ratio = round(live_vol / avg_vol, 1) if avg_vol > 0 else 1.0

        risk = max(live_price - box_bottom, 1.0)
        qty = max(int((capital * 0.01) / risk), 1)

        # सिग्नल
        if live_price > box_top and live_price > ema_20 and vol_ratio >= 1.2 and width <= 18:
            signal = "BUY"
        elif live_price < box_bottom:
            signal = "EXIT"
        else:
            signal = "HOLD"

        return {
            "Stock": sym,
            "Signal": signal,
            "Live Price (₹)": round(live_price, 2),
            "Box Top": round(box_top, 2),
            "Box Bottom (SL)": round(box_bottom, 2),
            "Box Width": f"{round(width, 1)}%",
            "Volume": f"{vol_ratio}x",
            "Qty": qty
        }
    except Exception:
        return None

# टॉप 30 हाई-मोमेंटम स्टॉक्स (सुपर फास्ट लोड होंगे)
top_stocks = [
    "HAL", "BEL", "TRENT", "ZOMATO", "DIXON", "POLYCAB", "CUMMINSIND", "PERSISTENT",
    "RELIANCE", "SBIN", "BHARTIARTL", "LT", "BAJFINANCE", "M&M", "SUNPHARMA", "TITAN",
    "TATAMOTORS", "ADANIENT", "COALINDIA", "TATASTEEL", "DLF", "SIEMENS", "ABB",
    "CHOLAFIN", "VEDL", "MUTHOOTFIN", "SHRIRAMFIN", "HCLTECH", "NTPC", "POWERGRID"
]

portfolio = st.text_input("💼 आपके खरीदे हुए शेयर (Track करने के लिए):", value="HAL, SBIN")

if st.button("🚀 लाइव स्कैन करें", use_container_width=True):
    with st.spinner("स्कैनिंग चालू है..."):
        results = []
        my_holdings = [s.strip().upper() for s in portfolio.split(",") if s.strip()]

        for sym in top_stocks:
            data = scan_single(sym)
            if data:
                results.append(data)
                if data["Signal"] == "BUY":
                    send_alert(f"BUY ALERT: {sym} @ ₹{data['Live Price (₹)']}", f"Box Top Breakout! SL: ₹{data['Box Bottom (SL)']} | Qty: {data['Qty']}")
                elif data["Signal"] == "EXIT" and sym in my_holdings:
                    send_alert(f"EXIT ALERT: {sym}", f"Box Bottom टूट गया! बाहर निकलें!")

        if results:
            res_df = pd.DataFrame(results)
            t1, t2, t3 = st.tabs(["🟢 BUY (खरीदें)", "🟡 HOLD (होल्ड)", "🔴 EXIT (निकलें)"])
            with t1:
                b_df = res_df[res_df["Signal"] == "BUY"]
                st.dataframe(b_df if not b_df.empty else pd.DataFrame([{"सूचना": "अभी कोई ब्रेकआउट नहीं मिला"}]))
            with t2:
                st.dataframe(res_df[res_df["Signal"] == "HOLD"])
            with t3:
                e_df = res_df[res_df["Signal"] == "EXIT"]
                st.dataframe(e_df if not e_df.empty else pd.DataFrame([{"सूचना": "कोई शेयर खतरे में नहीं है"}]))
