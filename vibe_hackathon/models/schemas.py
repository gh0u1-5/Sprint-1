from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class SignalType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class RiskTolerance(str, Enum):
    AGGRESSIVE = "Aggressive"
    CONSERVATIVE = "Conservative"


class AgentSignal(BaseModel):
    agent_name: str
    stock_symbol: str
    signal: SignalType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: str
    citations: List[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    risk_tolerance: RiskTolerance
    watchlist: List[str] = Field(default_factory=list)