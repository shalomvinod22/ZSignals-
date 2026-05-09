"""Signal classifier for Zintlr Pulse.

Lightweight pre-classifier that tags posts with implicit signal types
before Groq qualification. Runs very fast (regex/keyword based).
"""

import re
from typing import Optional


# Regex patterns for signal detection
COMPLAINT_PATTERNS = [
    r"\b(bouncing|bounce\s+rate|wrong\s+numbers|bad\s+data|inaccurate|data\s+quality|frustrated|waste|wasted|useless|terrible|terrible|sucks|hate|regret)\b",
]

HIRING_PATTERNS = [
    r"\b(hiring|hiring\s+sdr|hiring\s+bdr|first\s+sdr|expanding\s+sales|sales\s+team|looking\s+for\s+sdr|we\s+need|seeking\s+sdr|looking\s+to\s+hire)\b",
]

COMPARISON_PATTERNS = [
    r"\b(alternatives?\s+to|vs\s+apollo|evaluating|comparing|best\s+b2b\s+data|switch(ing)?|switched|moved\s+from|trying\s+out|testing|shopping\s+for)\b",
]

STACK_PATTERNS = [
    r"\b(our\s+process|we\s+use|currently\s+using|our\s+outbound\s+stack|our\s+tech\s+stack|we\s+built|tools\s+we\s+use)\b",
]

WISHLIST_PATTERNS = [
    r"\b(i\s+wish|is\s+there\s+a|anyone\s+know|looking\s+for|does\s+anyone\s+have|need\s+a\s+tool|need\s+something)\b",
]

VP_HIRE_PATTERNS = [
    r"\b(new\s+vp\s+sales|vp\s+of\s+sales|joined\s+as\s+vp|head\s+of\s+sales|vp\s+sales\s+started)\b",
]

FUNDING_PATTERNS = [
    r"\b(series\s+a|series\s+b|series\s+c|raised|closed\s+funding|funding\s+round|just\s+closed|seed\s+round)\b",
]


class SignalClassifier:
    """Classifies implicit signals in post content."""

    @staticmethod
    def _match_pattern(text: str, patterns: list[str]) -> bool:
        """Check if any pattern matches in text (case-insensitive)."""
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    @staticmethod
    def classify(content: str) -> list[str]:
        """Detect signal types in content.
        
        Args:
            content: Post/comment text to analyze.
            
        Returns:
            List of signal types found: "complaint", "hiring", "comparison_shopping",
            "stack_describing", "wishlist", "vp_hire", "funding".
            Empty list if no signals detected.
        """
        if not content or not isinstance(content, str):
            return []
        
        signals = []
        
        if SignalClassifier._match_pattern(content, COMPLAINT_PATTERNS):
            signals.append("complaint")
        
        if SignalClassifier._match_pattern(content, HIRING_PATTERNS):
            signals.append("hiring")
        
        if SignalClassifier._match_pattern(content, COMPARISON_PATTERNS):
            signals.append("comparison_shopping")
        
        if SignalClassifier._match_pattern(content, STACK_PATTERNS):
            signals.append("stack_describing")
        
        if SignalClassifier._match_pattern(content, WISHLIST_PATTERNS):
            signals.append("wishlist")
        
        if SignalClassifier._match_pattern(content, VP_HIRE_PATTERNS):
            signals.append("vp_hire")
        
        if SignalClassifier._match_pattern(content, FUNDING_PATTERNS):
            signals.append("funding")
        
        return signals
