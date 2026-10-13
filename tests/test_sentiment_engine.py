"""
Integration Test Suite for Person 3: Sentiment Analysis Engine
Validates VADER sentiment score parsing and polarity categorization.
"""

import pytest
from src.sentiment_analysis import analyze_text_sentiment


def test_positive_sentiment():
    headline = "Reliance Industries reports record-breaking quarterly net profit growth"
    res = analyze_text_sentiment(headline)
    assert "compound" in res
    assert res["compound"] > 0
    assert res["label"] in ["Bullish", "Positive"]


def test_negative_sentiment():
    headline = "Stock plunges 15% amid severe regulatory penalty and earnings slump"
    res = analyze_text_sentiment(headline)
    assert "compound" in res
    assert res["compound"] < 0
    assert res["label"] in ["Bearish", "Negative"]
