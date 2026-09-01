import os
import json
import random
from datetime import datetime, timedelta

def generate_mock_data():
    # 1. Ensure /data directory exists
    data_dir = os.path.join(".", "data")
    os.makedirs(data_dir, exist_ok=True)

    # 2. Generate simulated tick data for NSE stocks
    stocks_config = {
        "RELIANCE": {"base_price": 1280.0, "volatility": 1.5, "avg_volume": 150},
        "INFOSYS": {"base_price": 1130.0, "volatility": 1.2, "avg_volume": 100},
        "TCS": {"base_price": 2390.0, "volatility": 2.0, "avg_volume": 80}
    }

    start_time = datetime(2026, 9, 1, 9, 15, 0) # NSE Market Open
    tick_records = []
    
    # Generate 50 simulated trading ticks per stock
    for symbol, config in stocks_config.items():
        current_price = config["base_price"]
        for i in range(50):
            timestamp = (start_time + timedelta(seconds=i * 5)).strftime("%Y-%m-%d %H:%M:%S")
            price_change = round(random.uniform(-config["volatility"], config["volatility"]), 2)
            current_price = round(max(10.0, current_price + price_change), 2)
            volume = random.randint(10, config["avg_volume"] * 5)
            trade_type = random.choice(["BUY", "SELL"])

            tick_records.append({
                "symbol": symbol,
                "exchange": "NSE",
                "timestamp": timestamp,
                "price": current_price,
                "volume": volume,
                "side": trade_type,
                "currency": "INR"
            })

    # Sort ticks chronologically
    tick_records.sort(key=lambda x: x["timestamp"])

    # Write tick data JSON
    json_path = os.path.join(data_dir, "nse_ticks.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tick_records, f, indent=2)

    # 3. Generate SEBI Corporate Filings text file
    sebi_filings_content = """================================================================================
SECURITIES AND EXCHANGE BOARD OF INDIA (SEBI) CORPORATE DISCLOSURE FILING
================================================================================
Filing Ref ID: SEBI/NSE/2026/Q2-DISC-0912
Date of Submission: September 01, 2026
Applicable Regulation: SEBI (LODR) Regulations, 2015 - Regulation 30 & 33

SECTION I: CORPORATE ANNOUNCEMENTS & DISCLOSURES

1. RELIANCE INDUSTRIES LIMITED (Symbol: RELIANCE)
   - Note on Expansion: Approval granted for an additional capital expenditure 
     of INR 15,000 Crore towards expansion of green energy giga-factories in Jamnagar.
   - Regulatory Compliance: Pursuant to SEBI Circular SEBI/HO/CFD/CMD1/CIR/P/2023/123, 
     the company confirms no pending material litigations impacting Q2 operational income.
   - Financial Note: Net operational debt reduced by 4.2% YoY. Debt-to-Equity 
     ratio maintained within target threshold of 0.35x.

2. TATA CONSULTANCY SERVICES LIMITED (Symbol: TCS)
   - Strategic Contract Win: Multi-year partnership renewal valued at $450 Million 
     with a leading European financial services group for Cloud Transformation & AI deployment.
   - Financial Note: Operating margin targeted at 24.5% - 25.2% for FY27 despite wage 
     hike headwinds. Dividend payout ratio remains aligned with 80%+ free cash flow distribution policy.

3. INFOSYS LIMITED (Symbol: INFY)
   - Share Buyback Update: Completion of mandatory disclosure under SEBI Buyback 
     Regulations. Total shares extinguished: 12,500,000 at an aggregate consideration of INR 1,800 Crore.

================================================================================
SECTION II: STATUTORY RISK FACTORS (SEBI MANDATED)
================================================================================
Risk Factor 1 - Foreign Exchange Fluctuation:
IT sector issuers (TCS, INFOSYS) maintain substantial revenue exposure to USD/EUR/GBP. 
Unhedged volatility in cross-currency rates may adversely impact operating margins.

Risk Factor 2 - Commodity Price Volatility & Refining Margins:
Energy sector issuers (RELIANCE) remain exposed to global crude benchmark swings and Gross 
Refining Margin (GRM) fluctuations governed by macroeconomic geopolitical dynamics.

Risk Factor 3 - Regulatory & Compliance Changes:
Modifications to Indian tax structures (MAT/GST), cross-border data sovereignty norms, 
or foreign labor visa regulations pose ongoing operational compliance risks.
================================================================================
"""
    sebi_path = os.path.join(data_dir, "sebi_corporate_filings.txt")
    with open(sebi_path, "w", encoding="utf-8") as f:
        f.write(sebi_filings_content)

    # 4. Generate Earnings Transcripts text file
    transcripts_content = """================================================================================
Q2 FY2026 EARNINGS CONFERENCE CALL TRANSCRIPTS & MANAGEMENT NOTES
================================================================================
Date: August 28, 2026
Participants: Executive Management Teams & Institutional Financial Analysts

--------------------------------------------------------------------------------
EXCERPT 1: TATA CONSULTANCY SERVICES (TCS) MANAGEMENT COMMENTARY
--------------------------------------------------------------------------------
Chief Executive Officer:
"We delivered steady constant-currency growth this quarter, driven by strong 
demand for enterprise AI integration and infrastructure modernization. Total Contract 
Value (TCV) signed during the quarter stood at $8.2 Billion."

Chief Financial Officer (Notes on Margins & Capital Allocation):
"Subcontractor costs have normalized to 7.1% of revenue. Our utilization rate 
exceeded 85.4%. Free Cash Flow generation remains exceptionally robust at INR 11,200 Crore. 
We reaffirm our long-term operating margin band of 26-28%."

Analyst Question: "What are the major risk factors visible in discretionary tech spending?"
Management Response: "Macro uncertainties in Europe have caused extended deal-closure 
cycles in capital market verticals. However, cost-optimization programs continue to offset 
slower discretionary transformation projects."

--------------------------------------------------------------------------------
EXCERPT 2: RELIANCE INDUSTRIES LIMITED (RIL) MANAGEMENT COMMENTARY
--------------------------------------------------------------------------------
Joint Managing Director:
"Our Oil-to-Chemicals (O2C) segment demonstrated resilience despite global margin 
compression. Digital Services (Jio) recorded steady ARPU expansion to INR 188.5."

Chief Financial Officer (Financial Notes):
"Consolidated EBITDA for the quarter reached INR 42,500 Crore. Retail footprint 
expanded with 310 new stores opened. Capex for the quarter was INR 23,100 Crore, funded 
predominantly through internal accruals."

Key Risk Factor Highlighted:
"Geopolitical tensions impacting global energy supply chains and potential tariff 
adjustments in telecom remain primary monitoring points for the upcoming quarters."

--------------------------------------------------------------------------------
EXCERPT 3: INFOSYS LIMITED MANAGEMENT COMMENTARY
--------------------------------------------------------------------------------
Chief Financial Officer:
"Large deal TCV was $2.4 Billion with 55% net new wins. Attrition further stabilized to 12.3%. 
We maintain our full-year revenue growth guidance of 3.0% - 4.5% in CC terms."
================================================================================
"""
    transcripts_path = os.path.join(data_dir, "earnings_transcripts.txt")
    with open(transcripts_path, "w", encoding="utf-8") as f:
        f.write(transcripts_content)

    print(f"Data generation complete!")
    print(f"  - Ticks JSON: {os.path.abspath(json_path)}")
    print(f"  - SEBI Filings: {os.path.abspath(sebi_path)}")
    print(f"  - Transcripts: {os.path.abspath(transcripts_path)}")

if __name__ == "__main__":
    generate_mock_data()