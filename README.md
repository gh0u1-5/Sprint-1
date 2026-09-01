FinEX: Your Financial Expert

Problem Statement:-\ 
Design a multi-agent AI system that converts real-me market data, regulatory filings, and behavioral signals into explainable, personalized investment intelligence for retail investors — bridging the gap between raw financial data and ac onable decision-making. The system should not just surface what is happening in the market, but reason about what it means for a specific user's financial position, and be able to justify that reasoning transparently at every step. 
Who are the Users?\
1. Primary Retail Investors\
--Beginner / DIY Investors: Individuals seeking plain-language explanations of complex SEC filings (10-Ks, 10-Qs) and market news without getting overwhelmed by financial jargon.\
--Active / Self-Directed Traders: Traders who need real-time sentiment analysis, regulatory filing extraction, and signal correlation faster than manual research permits. \
--Goal-Oriented Long-Term Investors: Savers building towards specific milestones (e.g., retirement, homeownership) who require personalized portfolio impact analysis tied directly to their personal risk tolerance. \

2. Secondary & Operational Stakeholders\
--Financial Advisors & Wealth Managers: Professionals who utilize the platform’s transparent "chain-of-thought" reasoning logs to clearly explain market shifts and portfolio adjustments to clients.\
--Compliance & Risk Managers: System auditors who review multi-agent reasoning trails to guard against hallucinations and ensure strict regulatory adherence \

Features:-\--Multi-Agent Signal Engine: Specialized agents analyze technical indicators, fundamental filings, and market sentiment in parallel to synthesize actionable recommendations.\
--Explainable AI Reasoning (XAI): Step-by-step transparency into why a signal was generated, breaking down complex data into user-understandable rationale.\
--Personalized Risk Profiling: Customizes market impact analysis based on individual user risk parameters (Conservative, Moderate, Aggressive Growth).\
--Real-Time Data Ingestion: Live price streams, historical market performance, and multi-currency conversion (INR, USD, EUR, GBP).\
--Quantitative Risk Analytics: Dynamic calculation of annualized volatility, 95% Value-at-Risk (VaR), and position risk concentration.\
--Context-Aware AI Assistant: Interactive chat interface powered by Gemini 3.6 Flash that retains profile, ticker, and market context for tailored financial advisory.\
--Portfolio Simulation Calculator: Interactive PnL and return projections based on holding duration and historical return distributions.\
--Secure Telemetry & Auth: Encrypted user management, IP-based session control, and real-time query latency logging

FinEX Technology Stack\
Frontend & Application Framework\
--Streamlit: Renders the web interface, manages state (`st.session_state`), handles interactive inputs, and controls page layout.
==Custom CSS & HTML Injection: Injected via `st.markdown` to achieve custom dark-mode styling, grid background overlays, and tailored component cards.


Backend & Data Storage\
--Python 3: Serves as the core application logic and execution engine.
--SQLite3: Embedded relational database for persistent user accounts, session tracking, portfolio storage, and real-time performance telemetry logs.
--SHA-256: Handles secure client authentication and password hashing.

Data Processing & Financial Data Feeds\
--yfinance: Delivers real-time and historical stock market data retrieval for National Stock Exchange (NSE) tickers and Forex exchange rates.
--NumPy: Computes quantitative metrics including logarithmic returns, annualized volatility calculations, and 95% Value-at-Risk (VaR) estimations.

Data Visualization\
--Plotly:Renders interactive price charts featuring custom dark templates, dynamic color fills, and unified hover tooltips.\

Artificial Intelligence & Multi-Agent Engine\
--Google Gemini API: Powers the interactive AI conversational assistant (`gemini-1.5-flash`) with dynamic, profile-aware contextual prompting.\

Instructions:\
In the terminal of app.py type "python -m streamlit app.py"

Team Members\
--Abishek S Ashok\
--Anushree Nair\
--Mohammed Ameen \
--Sharanya Vimal Nair\
--Sidharth Sebin Roy

