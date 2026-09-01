import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class AgentSignal:
    symbol: str
    signal: SignalType
    confidence: float  # Normalized 0.0 to 1.0
    agent_name: str
    reasoning: str


def run_technical_agent(stock_symbol: str, data_dir: str = "/data") -> AgentSignal:
    """
    Reads JSON ticks for a stock symbol from data_dir, evaluates price and volume trends,
    and returns an AgentSignal.
    """
    symbol_upper = stock_symbol.upper()
    file_path = Path(data_dir) / f"{symbol_upper}.json"

    # Handle missing data file gracefully
    if not file_path.exists():
        return AgentSignal(
            symbol=symbol_upper,
            signal=SignalType.HOLD,
            confidence=0.0,
            agent_name="TechnicalAgent",
            reasoning=f"No tick data found at path: {file_path}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        ticks: List[Dict[str, Any]] = data if isinstance(data, list) else data.get("ticks", [])
    except Exception as e:
        return AgentSignal(
            symbol=symbol_upper,
            signal=SignalType.HOLD,
            confidence=0.0,
            agent_name="TechnicalAgent",
            reasoning=f"Failed to read or parse tick data: {str(e)}"
        )

    if len(ticks) < 2:
        return AgentSignal(
            symbol=symbol_upper,
            signal=SignalType.HOLD,
            confidence=0.1,
            agent_name="TechnicalAgent",
            reasoning="Insufficient tick data to perform trend analysis (less than 2 ticks)."
        )

    # Analyze short-term price and volume movement
    recent_ticks = ticks[-10:]  # Focus on the latest window of ticks
    first_tick = recent_ticks[0]
    last_tick = recent_ticks[-1]

    price_start = float(first_tick.get("price", 0))
    price_end = float(last_tick.get("price", 0))
    
    price_change_pct = ((price_end - price_start) / price_start) * 100 if price_start > 0 else 0

    # Calculate average volume change relative to start
    volumes = [float(t.get("volume", 0)) for t in recent_ticks]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    recent_volume = volumes[-1]
    
    volume_surge = (recent_volume > avg_volume * 1.2) if avg_volume > 0 else False

    # Determine Signal Logic
    if price_change_pct > 1.5 and volume_surge:
        signal = SignalType.BUY
        confidence = min(0.85, 0.5 + (price_change_pct / 100))
        reasoning = f"Price increased by {price_change_pct:.2f}% with high volume surge."
    elif price_change_pct < -1.5 and volume_surge:
        signal = SignalType.SELL
        confidence = min(0.85, 0.5 + (abs(price_change_pct) / 100))
        reasoning = f"Price decreased by {price_change_pct:.2f}% with elevated volume selling."
    elif price_change_pct > 0.5:
        signal = SignalType.BUY
        confidence = 0.55
        reasoning = f"Moderate upward price movement ({price_change_pct:.2f}%)."
    elif price_change_pct < -0.5:
        signal = SignalType.SELL
        confidence = 0.55
        reasoning = f"Moderate downward price movement ({price_change_pct:.2f}%)."
    else:
        signal = SignalType.HOLD
        confidence = 0.50
        reasoning = f"Price trajectory remains sideways ({price_change_pct:.2f}%)."

    return AgentSignal(
        symbol=symbol_upper,
        signal=signal,
        confidence=round(confidence, 2),
        agent_name="TechnicalAgent",
        reasoning=reasoning
    )