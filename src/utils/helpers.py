"""Helper utility functions"""

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import tiktoken


def generate_id(text: str) -> str:
    """Generate a unique ID from text using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.,!?;:\-\(\)\'\"]+', '', text)
    
    return text.strip()


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text for a specific model"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to approximate count
        return len(text.split()) * 1.3


def truncate_text(text: str, max_tokens: int = 8000, model: str = "gpt-4") -> str:
    """Truncate text to fit within token limit"""
    tokens = count_tokens(text, model)
    
    if tokens <= max_tokens:
        return text
    
    # Estimate characters per token
    chars_per_token = len(text) / tokens
    max_chars = int(max_tokens * chars_per_token * 0.95)  # 95% to be safe
    
    return text[:max_chars] + "..."


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime"""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract top keywords from text (simple version)"""
    # Remove stopwords (simplified)
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Tokenize and filter
    words = re.findall(r'\b[a-z]+\b', text.lower())
    words = [w for w in words if w not in stopwords and len(w) > 3]
    
    # Count frequency
    word_freq: Dict[str, int] = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top N
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def format_paper_metadata(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Format paper metadata for display"""
    return {
        "id": paper.get("id", ""),
        "title": paper.get("title", "Untitled"),
        "authors": ", ".join(paper.get("authors", [])[:3]) + (
            "..." if len(paper.get("authors", [])) > 3 else ""
        ),
        "published": paper.get("published", "Unknown"),
        "abstract": paper.get("abstract", "")[:200] + "...",
        "url": paper.get("url", ""),
        "citations": paper.get("citations", 0),
    }


def save_json(data: Any, filepath: str):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return url_pattern.match(url) is not None
