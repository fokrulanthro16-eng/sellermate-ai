"""
Intent detection using rapidfuzz fuzzy matching.
Falls back to substring matching if rapidfuzz is unavailable.
No external API required.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz, process as rf_process
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False


@dataclass
class IntentResult:
    intent: str
    confidence: float   # 0.0 – 1.0
    lang: str           # "bn" | "en"


# ── Keyword banks per intent ───────────────────────────────
# Each list contains Bangla and English terms that strongly
# signal that specific intent.  The fuzzy matcher scores the
# whole user message against every keyword and picks the
# highest-scoring (intent, keyword) pair.

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "greeting": [
        "হ্যালো", "হ্যাই", "হেলো", "সালাম", "আস্সালামু আলাইকুম", "নমস্কার",
        "hello", "hi", "hey", "salam", "greetings", "good morning", "good evening",
    ],
    "help": [
        "সাহায্য", "কী পারো", "কি করতে পারো", "কী জিজ্ঞেস করব",
        "help", "what can you do", "what do you know", "capabilities", "commands",
    ],
    "low_stock": [
        "কম স্টক", "স্টক শেষ", "স্টকশূন্য", "ইনভেন্টরি কম", "কোন পণ্য নেই",
        "স্টক কত", "পণ্য শেষ", "স্টক চেক",
        "low stock", "out of stock", "inventory alert", "stock level",
        "which product is low", "stock check", "inventory",
    ],
    "top_products": [
        "শীর্ষ পণ্য", "সবচেয়ে বেশি বিক্রি", "বেস্ট পণ্য", "কোন পণ্য ভালো",
        "জনপ্রিয় পণ্য", "বেশি বিক্রয়", "সেরা পণ্য",
        "top products", "best selling", "most sold", "popular products",
        "which product sells most", "top sellers", "best products",
    ],
    "revenue_summary": [
        "রাজস্ব", "আয়", "বিক্রয় সারাংশ", "কত টাকা", "মোট আয়",
        "এই মাসে কত", "গত সপ্তাহে কত", "মোট রাজস্ব",
        "revenue", "income", "earnings", "total revenue", "how much earned",
        "sales summary", "financial summary", "profit",
    ],
    "order_summary": [
        "অর্ডার", "মোট অর্ডার", "কতটি অর্ডার", "আজকের অর্ডার",
        "পেন্ডিং অর্ডার", "ডেলিভার অর্ডার", "বাতিল অর্ডার", "অর্ডার রিপোর্ট",
        "orders", "order count", "pending orders", "delivered orders",
        "cancelled orders", "order report", "recent orders",
    ],
    "best_customers": [
        "শীর্ষ গ্রাহক", "ভিআইপি গ্রাহক", "সেরা গ্রাহক", "নিয়মিত গ্রাহক",
        "কে বেশি কেনে", "গ্রাহক তথ্য", "গ্রাহক",
        "top customers", "best customers", "vip customers", "loyal customers",
        "who buys most", "customer info", "repeat customers", "customers",
    ],
    "trust_score": [
        "ট্রাস্ট স্কোর", "বিশ্বাসযোগ্যতা", "ট্রাস্ট", "ব্যবসার মান",
        "trust score", "trust rating", "business trust", "credibility",
    ],
    "fraud_risk": [
        "ফ্রড", "জালিয়াতি", "সন্দেহজনক অর্ডার", "ফ্রড ঝুঁকি",
        "fraud", "fraud risk", "suspicious orders", "scam risk",
    ],
    "restock_advice": [
        "কী অর্ডার করব", "কোন পণ্য কিনব", "রিস্টক পরামর্শ", "স্টক বাড়াব",
        "রিস্টক", "কী কিনব",
        "what to restock", "restock advice", "which to order", "inventory advice",
        "reorder", "what should i buy",
    ],
    "growth_advice": [
        "ব্যবসা বাড়ানো", "প্রবৃদ্ধি", "উন্নতি করব কীভাবে", "বিক্রয় বাড়াব",
        "কী করলে ভালো হবে", "কৌশল", "পরামর্শ",
        "grow business", "growth advice", "how to improve", "increase sales",
        "strategy", "tips", "recommendations", "growth",
    ],
    "today_summary": [
        "আজ", "আজকের", "আজকে", "সারাংশ", "ওভারভিউ",
        "today", "today's summary", "today overview", "current status", "summary",
    ],
}

# Flat lookup: keyword → intent
_KW_TO_INTENT: dict[str, str] = {}
_ALL_KWS: list[str] = []
for _intent, _kws in _INTENT_KEYWORDS.items():
    for _kw in _kws:
        _KW_TO_INTENT[_kw.lower()] = _intent
        _ALL_KWS.append(_kw.lower())


def _detect_lang(text: str) -> str:
    return "bn" if re.search(r"[ঀ-৿]", text) else "en"


def detect_intent(text: str) -> IntentResult:
    """
    Return the most likely intent for the given user message.

    Algorithm:
    1. rapidfuzz partial_ratio match against the full keyword list → highest score wins.
    2. Exact/substring fallback when rapidfuzz is unavailable or score is too low.
    3. Default to 'today_summary' if nothing matches.
    """
    lang = _detect_lang(text)
    text_lower = text.lower().strip()

    # ── rapidfuzz path ──────────────────────────────────────
    if _HAS_RAPIDFUZZ:
        match = rf_process.extractOne(
            text_lower,
            _ALL_KWS,
            scorer=fuzz.partial_ratio,
            score_cutoff=55,
        )
        if match:
            matched_kw, score, _ = match
            intent = _KW_TO_INTENT.get(matched_kw, "today_summary")
            return IntentResult(intent=intent, confidence=score / 100.0, lang=lang)

    # ── substring fallback ──────────────────────────────────
    for kw, intent in _KW_TO_INTENT.items():
        if kw in text_lower:
            return IntentResult(intent=intent, confidence=0.75, lang=lang)

    return IntentResult(intent="today_summary", confidence=0.3, lang=lang)
