from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import concurrent.futures

# --- Mock/Type Definitions (Adjust imports as needed for your project structure) ---

@dataclass
class UserProfile:
    risk_tolerance: str  # e.g., 'Conservative', 'Moderate', 'Aggressive'
    investment_horizon: str = 'Long-term'

# Example agent function signatures (replace with your actual module imports):
# from agents.technical import analyze_technical
# from agents.fundamental import analyze_fundamental
# from agents.sentiment import analyze_sentiment

def analyze_technical(stock_symbol: str) -> Dict[str, Any]:
    """Mock technical analysis agent."""
    return {"signal": "BULLISH", "confidence": 0.85, "details": "RSI overbought, strong trend"}

def analyze_fundamental(stock_symbol: str) -> Dict[str, Any]:
    """Mock fundamental analysis agent."""
    return {"signal": "BULLISH", "confidence": 0.78, "details": "Strong earnings growth"}

def analyze_sentiment(stock_symbol: str) -> Dict[str, Any]:
    """Mock sentiment analysis agent."""
    return {"signal": "NEUTRAL", "confidence": 0.60, "details": "Mixed news coverage"}


# --- Main Synthesizer Implementation ---

def synthesize_investment_decision(stock_symbol: str, user_profile: UserProfile) -> Dict[str, Any]:
    """
    Executes technical, fundamental, and sentiment agents concurrently,
    aggregates their outputs, and applies risk management rules based on
    the user's profile.
    """
    # 1. Concurrently run technical, fundamental, and sentiment agents
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_tech = executor.submit(analyze_technical, stock_symbol)
        future_fund = executor.submit(analyze_fundamental, stock_symbol)
        future_sent = executor.submit(analyze_sentiment, stock_symbol)

        # Retrieve results
        results = {
            "technical": future_tech.result(),
            "fundamental": future_fund.result(),
            "sentiment": future_sent.result()
        }

    notes: List[str] = []

    # 2. Extract signals
    tech_signal = results["technical"].get("signal", "NEUTRAL").upper()
    fund_signal = results["fundamental"].get("signal", "NEUTRAL").upper()
    sent_signal = results["sentiment"].get("signal", "NEUTRAL").upper()

    # Determine aggregated majority/consensus signal before risk adjustments
    signals = [tech_signal, fund_signal, sent_signal]
    bullish_count = signals.count("BULLISH")
    bearish_count = signals.count("BEARISH")

    if bullish_count > bearish_count and bullish_count >= 2:
        aggregated_signal = "BULLISH"
    elif bearish_count > bullish_count and bearish_count >= 2:
        aggregated_signal = "BEARISH"
    else:
        aggregated_signal = "HOLD/NEUTRAL"

    # 3. Apply Conservative risk tolerance rule to downgrade volatile BULLISH signals
    if user_profile.risk_tolerance.title() == "Conservative":
        if aggregated_signal == "BULLISH":
            aggregated_signal = "HOLD/NEUTRAL"
            notes.append(
                "Downgraded aggregated BULLISH signal to HOLD/NEUTRAL due to 'Conservative' "
                "risk tolerance profile to mitigate market volatility exposure."
            )

    return {
        "stock_symbol": stock_symbol,
        "final_recommendation": aggregated_signal,
        "user_risk_tolerance": user_profile.risk_tolerance,
        "agent_outputs": results,
        "notes": notes
    }


# --- Quick Test Execution ---
if __name__ == "__main__":
    profile = UserProfile(risk_tolerance="Conservative")
    decision = synthesize_investment_decision("AAPL", profile)
    print(decision)