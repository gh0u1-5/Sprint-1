import os
from typing import Dict, List, Any
from pydantic import BaseModel, Field

# Assuming your central schema definitions location
# Adjust imports according to your project structure
from rag.vector_db import search_documents


class SourceCitation(BaseModel):
    document_name: str
    filing_type: str  # e.g., "SEBI Filing", "Earnings Call Transcript", "Annual Report"
    period: str       # e.g., "Q3 FY26"
    excerpt: str


class AgentSignal(BaseModel):
    agent_name: str = "Fundamental Analysis Agent"
    stock_symbol: str
    signal: str  # "BULLISH", "BEARISH", or "NEUTRAL"
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    citations: List[SourceCitation] = Field(default_factory=list)


def run_fundamental_agent(stock_symbol: str) -> AgentSignal:
    """
    Analyzes fundamental metrics and SEBI/earnings filings for a given stock symbol,
    returning a structured AgentSignal complete with explicit source citations.
    """
    # 1. Query vector database for relevant SEBI filings and earnings context
    query = f"{stock_symbol} SEBI filings earnings financial results revenue growth debt margins"
    
    # search_documents should return chunks with metadata (doc_name, type, period, text, etc.)
    search_results = search_documents(query=query, top_k=5)

    if not search_results:
        return AgentSignal(
            stock_symbol=stock_symbol,
            signal="NEUTRAL",
            confidence_score=0.0,
            summary=f"No SEBI or earnings filings found in vector database for {stock_symbol}.",
            key_metrics={},
            citations=[]
        )

    # 2. Process retrieved documents into explicit citations
    citations: List[SourceCitation] = []
    retrieved_texts: List[str] = []

    for doc in search_results:
        metadata = doc.get("metadata", {})
        citation = SourceCitation(
            document_name=metadata.get("file_name", "Unknown Document"),
            filing_type=metadata.get("filing_type", "SEBI Filing / Financials"),
            period=metadata.get("period", "N/A"),
            excerpt=doc.get("text", "")[:200] + "..."  # Truncate for concise citation
        )
        citations.append(citation)
        retrieved_texts.append(doc.get("text", ""))

    # 3. Perform fundamental evaluation logic (Rule-based or LLM-driven synthesis)
    # Combine context for context evaluation
    combined_context = "\n---\n".join(retrieved_texts)
    
    # Basic rule-based key metric extraction / placeholder logic 
    # (Replace or augment with an LLM call if using standard LangChain/OpenAI pipelines)
    bullish_keywords = ["growth", "revenue increase", "profit", "expansion", "debt reduction"]
    bearish_keywords = ["loss", "revenue decline", "margin compression", "default", "investigation"]

    bullish_score = sum(combined_context.lower().count(kw) for kw in bullish_keywords)
    bearish_score = sum(combined_context.lower().count(kw) for kw in bearish_keywords)

    total_mentions = bullish_score + bearish_score
    
    if total_mentions == 0:
        signal_val = "NEUTRAL"
        confidence = 0.5
    elif bullish_score > bearish_score:
        signal_val = "BULLISH"
        confidence = min(0.95, round(0.5 + (bullish_score / (total_mentions + 5)), 2))
    else:
        signal_val = "BEARISH"
        confidence = min(0.95, round(0.5 + (bearish_score / (total_mentions + 5)), 2))

    summary_text = (
        f"Fundamental analysis for {stock_symbol} based on {len(citations)} retrieved "
        f"SEBI filings and earnings records. Overall sentiment trends {signal_val.lower()}."
    )

    # 4. Construct and return the finalized signal
    return AgentSignal(
        stock_symbol=stock_symbol,
        signal=signal_val,
        confidence_score=confidence,
        summary=summary_text,
        key_metrics={
            "retrieved_documents_count": len(citations),
            "bullish_indicators_found": bullish_score,
            "bearish_indicators_found": bearish_score,
        },
        citations=citations
    )


if __name__ == "__main__":
    # Quick execution sanity check
    test_symbol = "RELIANCE"
    # Note: Ensure rag.vector_db is accessible in your standard PYTHONPATH
    # signal_output = run_fundamental_agent(test_symbol)
    # print(signal_output.model_dump_json(indent=2))