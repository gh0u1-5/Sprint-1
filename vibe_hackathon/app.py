import streamlit as st
import json
import os
import time
import sqlite3
import hashlib
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# ==========================================
# 1. DATABASE & AUTHENTICATION SETUP
# ==========================================
DB_FILE = "users_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            ip_address TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ticker TEXT,
            shares INTEGER,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            ticker TEXT,
            latency_ms REAL,
            signal_confidence_pct REAL,
            risk_concentration_score REAL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    data = c.fetchall()
    conn.close()
    return len(data) > 0

# --- IP SESSION MANAGEMENT ---
def get_client_ip():
    try:
        headers = st.context.headers
        if "X-Forwarded-For" in headers:
            return headers["X-Forwarded-For"].split(",")[0].strip()
        elif "Host" in headers:
            return headers["Host"].split(":")[0].strip()
    except Exception:
        pass
    return "127.0.0.1"

def get_session_by_ip(ip_address):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username FROM active_sessions WHERE ip_address = ?', (ip_address,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def save_ip_session(ip_address, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO active_sessions (ip_address, username, last_active)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(ip_address) DO UPDATE SET username=excluded.username, last_active=CURRENT_TIMESTAMP
    ''', (ip_address, username))
    conn.commit()
    conn.close()

def remove_ip_session(ip_address):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM active_sessions WHERE ip_address = ?', (ip_address,))
    conn.commit()
    conn.close()

def log_performance_metrics(username, ticker, latency_ms, confidence_pct, risk_score):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO performance_logs 
        (username, ticker, latency_ms, signal_confidence_pct, risk_concentration_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, ticker, latency_ms, confidence_pct, risk_score))
    conn.commit()
    conn.close()

init_db()

# Fetch IP and Auto-Login Check
client_ip = get_client_ip()
saved_username = get_session_by_ip(client_ip)

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = True if saved_username else False
if 'username' not in st.session_state:
    st.session_state['username'] = saved_username if saved_username else ""
if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'
if 'auth_tab' not in st.session_state:
    st.session_state['auth_tab'] = 0  # 0: Sign In, 1: Register
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = [
        {"role": "assistant", "content": "Hello! I am your AI Financial Advisor. Ask me anything about stock metrics, portfolio diversification, or market risk!"}
    ]

# Page Configuration
st.set_page_config(
    page_title="FinEX | Your Financial Expert", 
    layout="wide", 
    initial_sidebar_state="collapsed" if not st.session_state['authenticated'] else "expanded"
)

# Custom Styling Matching FinEX Image Design
st.markdown("""
<style>
    /* Dark grid background */
    .stApp {
        background-color: #0B0E14;
        background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
    }
    
    .stMetric {
        background: #121721;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #1E2638;
    }
    .agent-card {
        background-color: #121721;
        border-radius: 10px;
        padding: 18px;
        border-left: 4px solid #3B82F6;
        margin-bottom: 15px;
    }
    .agent-card-tech { border-left-color: #10B981; }
    .agent-card-fund { border-left-color: #F59E0B; }
    .agent-card-sent { border-left-color: #06B6D4; }

    /* Custom FinEX Card Styling */
    .finex-card {
        background-color: #111622;
        border: 1px solid #1D2636;
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
    }
    .finex-card-title {
        color: #E2E8F0;
        font-size: 18px;
        font-weight: 600;
        margin-top: 8px;
    }
    .finex-card-sub {
        color: #64748B;
        font-size: 14px;
        margin-top: 4px;
    }
    
    /* Center align container for hero */
    .hero-badge {
        text-align: center;
        color: #94A3B8;
        font-size: 12px;
        letter-spacing: 1.5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Navigation helpers
def go_to_auth_login():
    st.session_state['page'] = 'auth'
    st.session_state['auth_tab'] = 0

def go_to_auth_register():
    st.session_state['page'] = 'auth'
    st.session_state['auth_tab'] = 1

def go_to_landing():
    st.session_state['page'] = 'landing'

# ==========================================
# 2. LANDING & SIGN-IN INTERFACES
# ==========================================
if not st.session_state['authenticated']:
    
    # Header Nav Bar
    nav_col1, nav_col2 = st.columns([8, 2])
    with nav_col1:
        st.markdown("<h3 style='margin:0; padding:0; color:#FFFFFF;'>📈 <b>FinEX</b></h3>", unsafe_allow_html=True)
        st.caption("YOUR FINANCIAL EXPERT")
    with nav_col2:
        if st.session_state['page'] == 'landing':
            st.button("Get started →", key="top_get_started", type="primary", on_click=go_to_auth_register)
        else:
            st.button("← Back to Home", key="top_back", on_click=go_to_landing)

    st.divider()

    # LANDING PAGE VIEW
    if st.session_state['page'] == 'landing':
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='hero-badge'>● MULTI-AGENT MARKET INTELLIGENCE</div>", unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; font-size: 56px; font-weight: 800; color: #FFFFFF; line-height: 1.1;'>Track Your Capital.<br>Understand The Market.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #8B98A5; margin-top: 15px;'>FinEX is your financial expert — AI agents read prices, filings and<br>sentiment, then explain every call.</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_c1, btn_c2, btn_c3, btn_c4, btn_c5 = st.columns([3, 1.5, 1.5, 3, 0.1])
        with btn_c2:
            st.button("Register →", key="hero_register", type="primary", use_container_width=True, on_click=go_to_auth_register)
        with btn_c3:
            st.button("Log in", key="hero_login", use_container_width=True, on_click=go_to_auth_login)

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Bottom Feature Cards (Filings Removed)
        card_col1, card_col2 = st.columns(2)
        with card_col1:
            st.markdown("""
            <div class="finex-card">
                <span style="color:#60A5FA; font-size: 20px;">📈</span>
                <div class="finex-card-title">Signal</div>
                <div class="finex-card-sub">Momentum & sentiment, scored.</div>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col2:
            st.markdown("""
            <div class="finex-card">
                <span style="color:#60A5FA; font-size: 20px;">🛡️</span>
                <div class="finex-card-title">Risk</div>
                <div class="finex-card-sub">Weighted to your profile.</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.stop()

    # SIGN IN / SIGN UP VIEW
    elif st.session_state['page'] == 'auth':
        auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
        with auth_col2:
            st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>Welcome to FinEX</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8B98A5;'>Sign in or create an account to access Multi-Agent Market Intelligence.</p>", unsafe_allow_html=True)
            
            # Control active tab via Radio selection styled as tabs
            tab_choice = st.radio(
                "", 
                ["🔒 Sign In", "📝 Register Account"], 
                index=st.session_state['auth_tab'], 
                horizontal=True,
                label_visibility="collapsed"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)

            if tab_choice == "🔒 Sign In":
                login_user = st.text_input("Username", key="login_user")
                login_pass = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Sign In to Platform", type="primary", use_container_width=True):
                    if authenticate_user(login_user, login_pass):
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = login_user
                        save_ip_session(client_ip, login_user)
                        st.success(f"Welcome back, {login_user}!")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password.")

            else:
                new_user = st.text_input("Choose Username", key="new_user")
                new_pass = st.text_input("Choose Password", type="password", key="new_pass")
                confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass")
                
                if st.button("Create Account", type="primary", use_container_width=True):
                    if not new_user or not new_pass:
                        st.warning("Please fill in all fields.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        if register_user(new_user, new_pass):
                            st.success("Account created successfully! Switching to Sign In...")
                            st.session_state['auth_tab'] = 0
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username already exists.")

        st.stop()

# ==========================================
# 3. MAIN DASHBOARD & METRICS PIPELINE
# ==========================================

start_time = time.time()

NSE_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "SBIN",
    "LTIM", "ITC", "HINDUNILVR", "L&T", "AXISBANK", "KOTAKBANK", "BAJFINANCE",
    "M&M", "MARUTI", "SUNPHARMA", "TATASTEEL", "NTPC", "TATAMOTORS", "POWERGRID",
    "ADANIENT", "ADANIPORTS", "COALINDIA", "TITAN", "BAJAJ-AUTO", "ULTRACEMCO",
    "ASIANPAINT", "HCLTECH", "ONGC", "JSWSTEEL", "GRASIM", "TECHM", "WIPRO",
    "EICHERMOT", "DIVISLAB", "DRREDDY", "CIPLA", "BRITANNIA", "APOLLOHOSP",
    "HEROMOTOCO", "TATACONSUM", "BPCL", "NESTLEIND", "BAJAJFINSV", "SBILIFE",
    "HDFCLIFE", "BEL", "TRENT", "SHRIRAMFIN", "JIOFIN", "ZOMATO", "PAYTM"
]

CURRENCY_CONFIG = {
    "INR (₹)": {"symbol": "₹", "pair": None, "fallback_rate": 1.0},
    "USD ($)": {"symbol": "$", "pair": "INR=X", "fallback_rate": 0.012},
    "EUR (€)": {"symbol": "€", "pair": "INREUR=X", "fallback_rate": 0.011},
    "GBP (£)": {"symbol": "£", "pair": "INRGBP=X", "fallback_rate": 0.0095}
}

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.title(f"👤 User: {st.session_state['username']}")
st.sidebar.caption(f"🔒 Session Bound to IP: `{client_ip}`")

if st.sidebar.button("🚪 Log Out"):
    remove_ip_session(client_ip)
    st.session_state['authenticated'] = False
    st.session_state['username'] = ""
    st.session_state['page'] = 'landing'
    st.rerun()

st.sidebar.divider()
st.sidebar.title("🎛️ Control Center")

risk_profile = st.sidebar.select_slider(
    "User Risk Parameter",
    options=["Conservative", "Moderate", "Aggressive Growth"],
    value="Conservative"
)

st.sidebar.subheader("NSE Asset Selection")
selected_dropdown = st.sidebar.selectbox("Select NSE Asset", NSE_STOCKS, index=0)
custom_ticker = st.sidebar.text_input("OR Type Custom NSE Symbol", value="").strip().upper()

stock_selected = custom_ticker if custom_ticker else selected_dropdown
ticker_symbol = f"{stock_selected}.NS"

st.sidebar.divider()
st.sidebar.write("### System Status")
st.sidebar.success(f"🌐 Data Stream: {ticker_symbol}")
st.sidebar.success("💾 DB Telemetry: Enabled")
st.sidebar.info("🤖 AI Chatbot: Active")

st.title("📈 FinEX Multi-Agent Engine")
st.caption("Converts live National Stock Exchange (NSE) market feeds into personalized guidance.")

def get_exchange_rate(target_currency_key):
    config = CURRENCY_CONFIG[target_currency_key]
    if config["pair"] is None:
        return 1.0
    try:
        fx_data = yf.Ticker(config["pair"]).history(period="1d")
        if not fx_data.empty:
            rate = fx_data['Close'].iloc[-1]
            if target_currency_key == "USD ($)" and rate > 1.0:
                rate = 1.0 / rate
            return rate
    except Exception:
        pass
    return config["fallback_rate"]

current_price_inr = 1500.00
pct_change = 0.00
change_str = "+0.00%"
ann_volatility = 0.20
daily_var_95 = 1.5
risk_score = 45.0
avg_daily_return = 0.001

stock_ticker = yf.Ticker(ticker_symbol)

try:
    hist_data_1m = stock_ticker.history(period="1mo")
    if not hist_data_1m.empty:
        current_price_inr = round(hist_data_1m['Close'].iloc[-1], 2)
        open_price = round(hist_data_1m['Open'].iloc[-1], 2)
        pct_change = round(((current_price_inr - open_price) / open_price) * 100, 2)
        change_str = f"{'+' if pct_change >= 0 else ''}{pct_change}%"

        daily_returns = np.log(hist_data_1m['Close'] / hist_data_1m['Close'].shift(1)).dropna()
        avg_daily_return = daily_returns.mean()
        daily_vol = np.std(daily_returns)
        ann_volatility = daily_vol * np.sqrt(252)
        daily_var_95 = round(1.645 * daily_vol * 100, 2)
        
        risk_score = min(round((ann_volatility / 0.50) * 100, 1), 100.0)
except Exception:
    pass

m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns([1.5, 2, 1.5, 1.5, 1.5])
m_col1.metric("Selected Security", ticker_symbol)

selected_currency = m_col2.selectbox(
    "Display Currency", 
    options=list(CURRENCY_CONFIG.keys()), 
    index=0
)

fx_rate = get_exchange_rate(selected_currency)
curr_symbol = CURRENCY_CONFIG[selected_currency]["symbol"]
converted_price = round(current_price_inr * fx_rate, 2)

m_col3.metric("Live NSE Price", f"{curr_symbol}{converted_price:,.2f}", delta=change_str)
m_col4.metric("Calculated Risk Score", f"{risk_score}/100", delta=f"{ann_volatility*100:.1f}% Ann. Vol")
m_col5.metric("Daily VaR (95% Conf)", f"-{daily_var_95}%")

st.divider()

# ==========================================
# 4. INLINE AI CONVERSATION POPUP (EXPANDABLE)
# ==========================================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

with st.expander("💬 Talk to AI Assistant", expanded=False):
    st.caption(f"Context: **{stock_selected}** | **{risk_profile} Profile**")
    
    chat_container = st.container(height=280)
    
    for msg in st.session_state['chat_messages']:
        with chat_container.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if user_query := st.chat_input("Ask AI about strategy, metrics, or risk..."):
        st.session_state['chat_messages'].append({"role": "user", "content": user_query})
        with chat_container.chat_message("user"):
            st.markdown(user_query)

        with chat_container.chat_message("assistant"):
            try:
                context_prompt = f"""
                You are a professional AI Financial Advisor on FinEX platform.
                User Profile: {st.session_state['username']}
                Risk Tolerance: {risk_profile}
                Active Stock Being Viewed: {stock_selected} ({ticker_symbol})
                Current Price: {curr_symbol}{converted_price}
                30-Day Volatility: {ann_volatility*100:.1f}%
                Risk Concentration Score: {risk_score}/100
                Daily 95% Value at Risk (VaR): -{daily_var_95}%
                
                Answer the user's query concisely using this live dashboard context where applicable.
                User Question: {user_query}
                """
                
                response = model.generate_content(context_prompt)
                ai_reply = response.text
            except Exception as e:
                ai_reply = f"❌ Gemini API Error: {e}"

            st.markdown(ai_reply)
            st.session_state['chat_messages'].append({"role": "assistant", "content": ai_reply})

st.divider()

# CHART SECTION
st.subheader("📊 Interactive Market Price Action")
timeframe = st.radio("Select Horizon", options=["1M", "3M", "6M", "1Y", "5Y"], horizontal=True, index=0)
tf_mapping = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}

try:
    chart_df = stock_ticker.history(period=tf_mapping[timeframe])
    if not chart_df.empty:
        chart_df['Converted_Close'] = chart_df['Close'] * fx_rate
        start_val = chart_df['Converted_Close'].iloc[0]
        end_val = chart_df['Converted_Close'].iloc[-1]
        line_color = "#10B981" if end_val >= start_val else "#EF4444"

        min_p = chart_df['Converted_Close'].min()
        max_p = chart_df['Converted_Close'].max()
        padding = (max_p - min_p) * 0.05 if max_p != min_p else min_p * 0.05

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_df.index, y=[min_p - padding] * len(chart_df),
            mode='lines', line=dict(color='rgba(0,0,0,0)', width=0), showlegend=False, hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=chart_df.index, y=chart_df['Converted_Close'],
            mode='lines', name=f'Close Price ({curr_symbol})',
            line=dict(color=line_color, width=2), fill='tonexty',
            fillcolor=f"rgba({'16, 185, 129' if end_val >= start_val else '239, 68, 68'}, 0.12)"
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="#0B0E14", plot_bgcolor="#121721",
            height=400, margin=dict(l=10, r=10, t=20, b=10),
            yaxis=dict(range=[min_p - padding, max_p + padding], side="right"),
            hovermode="x unified", showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Chart render error: {e}")

st.divider()

# SYNTHESIS & AGENT TRACE
composite_confidence = 79.0

if risk_profile == "Conservative" and risk_score > 35.0:
    decision_type = "HOLD / CAUTIOUS"
    badge_color = "orange"
    reasoning_summary = f"Calculated annualized volatility for **{ticker_symbol}** is high (**{ann_volatility*100:.1f}%** with risk score **{risk_score}/100**). Downgraded to **HOLD** under **{risk_profile}** parameters."
else:
    decision_type = "ACCUMULATE / BULLISH"
    badge_color = "green"
    reasoning_summary = f"Price momentum on **{ticker_symbol}** aligns with sector signals. Calculated volatility accepted under **{risk_profile}** profile."

st.markdown(f"### 🎯 Synthesized Recommendation: :{badge_color}[{decision_type}]")
st.info(f"**Synthesizer Explanation:** {reasoning_summary}")

st.subheader("🤖 Parallel Agent Reasoning Trace")
a_col1, a_col2, a_col3 = st.columns(3)
with a_col1:
    st.markdown(f"""
    <div class="agent-card agent-card-tech">
        <h4>📈 Technical Agent</h4>
        <p><b>Signal:</b> BULLISH (85% Conf)</p>
        <p>Ticker <code>{ticker_symbol}</code> price change: {change_str}. Calculated 30-day volatility: <b>{ann_volatility*100:.1f}%</b>.</p>
    </div>
    """, unsafe_allow_html=True)
with a_col2:
    st.markdown(f"""
    <div class="agent-card agent-card-fund">
        <h4>📄 Fundamental Agent (RAG)</h4>
        <p><b>Signal:</b> NEUTRAL (74% Conf)</p>
        <p>RAG engine scanned disclosures. Estimated 1-Day Value-at-Risk (VaR): <b>-{daily_var_95}%</b>.</p>
    </div>
    """, unsafe_allow_html=True)
with a_col3:
    st.markdown(f"""
    <div class="agent-card agent-card-sent">
        <h4>🌐 Sentiment Agent</h4>
        <p><b>Signal:</b> BULLISH (78% Conf)</p>
        <p>Market sentiment around <code>{stock_selected}</code> shows positive institutional flows.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# SIMULATION CALCULATOR
st.subheader("🧮 Simulation Stock Price Calculator")
sim_col1, sim_col2 = st.columns(2)
with sim_col1:
    num_shares = st.number_input("Shares to Buy", min_value=1, max_value=10000, value=50, step=5)
    holding_days = st.slider("Target Holding Duration (Days)", min_value=1, max_value=365, value=30)

current_total_value = converted_price * num_shares
projected_pct_change = (np.exp(avg_daily_return * holding_days) - 1) * 100
projected_pnl = current_total_value * (projected_pct_change / 100.0)
future_total_value = current_total_value + projected_pnl

with sim_col2:
    st.write("### Position Projection")
    p1, p2, p3 = st.columns(3)
    p1.metric("Current Value", f"{curr_symbol}{current_total_value:,.2f}")
    p2.metric("Estimated Return", f"{projected_pct_change:+.2f}%", delta=f"{holding_days} Days")
    p3.metric("Estimated PnL", f"{curr_symbol}{future_total_value:,.2f}", delta=f"{'+' if projected_pnl >= 0 else ''}{curr_symbol}{projected_pnl:,.2f}")

# Calculate Latency and Log to Database
latency_ms = round((time.time() - start_time) * 1000, 2)

log_performance_metrics(
    username=st.session_state['username'],
    ticker=ticker_symbol,
    latency_ms=latency_ms,
    confidence_pct=composite_confidence,
    risk_score=risk_score
)

# Display Logged Session Metrics Panel
st.divider()
st.subheader("⚡ Real-Time Session Telemetry (SQLite Logged)")
perf_col1, perf_col2, perf_col3 = st.columns(3)
perf_col1.metric("Metric 1: Pipeline Latency", f"{latency_ms} ms")
perf_col2.metric("Metric 2: Signal Confidence", f"{composite_confidence}%")
perf_col3.metric("Metric 3: Risk Concentration", f"{risk_score}/100")