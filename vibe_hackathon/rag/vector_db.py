"""
rag/vector_db.py

Module to load corporate filings and transcripts from /data, 
index them by paragraph, and search for relevant snippets using 
keyword relevance scoring.
"""

import math
import os
import re
from typing import Dict, List, Any

DATA_DIR = "/data"


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercased alphanumeric words."""
    return re.findall(r'\b\w+\b', text.lower())


def _load_documents(data_dir: str = DATA_DIR) -> List[Dict[str, Any]]:
    """
    Reads all .txt files from the target directory and parses them into paragraphs.
    
    Returns a list of paragraph metadata dictionaries containing:
    - filename: Name of the source file
    - start_line: 1-indexed line number where paragraph starts
    - text: Text content of the paragraph
    """
    paragraphs = []
    
    if not os.path.exists(data_dir):
        return paragraphs

    for file_name in sorted(os.listdir(data_dir)):
        if not file_name.endswith(".txt"):
            continue
            
        file_path = os.path.join(data_dir, file_name)
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        current_para = []
        para_start_line = 1

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped:
                if not current_para:
                    para_start_line = idx
                current_para.append(stripped)
            else:
                if current_para:
                    para_text = " ".join(current_para)
                    paragraphs.append({
                        "filename": file_name,
                        "start_line": para_start_line,
                        "text": para_text
                    })
                    current_para = []

        # Flush any remaining paragraph at EOF
        if current_para:
            para_text = " ".join(current_para)
            paragraphs.append({
                "filename": file_name,
                "start_line": para_start_line,
                "text": para_text
            })

    return paragraphs


def search_documents(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Searches through corporate filings in /data for keyword matches.

    Args:

        query_text (str): The search prompt or question.
        top_k (int): Number of top relevant snippets to return.

    Returns:
        List[Dict[str, Any]]: A list of up to top_k snippets with metadata:
            - source_file (str): Filename of source text
            - line_number (int): 1-indexed starting line number of paragraph
            - snippet (str): Paragraph content
            - score (float): Keyword relevance score
    """
    paragraphs = _load_documents(DATA_DIR)
    if not paragraphs:
        return []

    query_tokens = set(_tokenize(query_text))
    if not query_tokens:
        return []

    # Calculate Inverse Document Frequency (IDF) for query terms across paragraphs
    total_docs = len(paragraphs)
    idf: Dict[str, float] = {}
    
    for token in query_tokens:
        doc_freq = sum(1 for p in paragraphs if token in set(_tokenize(p["text"])))
        # TF-IDF calculation with smoothing
        idf[token] = math.log((total_docs + 1) / (doc_freq + 1)) + 1.0

    # Score each paragraph based on TF-IDF term weights
    scored_results = []
    for p in paragraphs:
        para_tokens = _tokenize(p["text"])
        if not para_tokens:
            continue
            
        score = 0.0
        for token in query_tokens:
            tf = para_tokens.count(token)
            if tf > 0:
                score += tf * idf[token]

        if score > 0:
            scored_results.append({
                "source_file": p["filename"],
                "line_number": p["start_line"],
                "snippet": p["text"],
                "score": round(score, 4)
            })

    # Sort descending by score
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]


if __name__ == "__main__":
    # Example usage / test run
    results = search_documents("revenue growth quarter", top_k=2)
    for r in results:
        print(f"[{r['source_file']}:Line {r['line_number']}] (Score: {r['score']})\n{r['snippet']}\n")