"""
Unit Test Suite for Person 2: Technical Indicators & Feature Engineering
Validates RSI, MACD, and Bollinger Bands calculation logic.
"""

import pandas as pd
import numpy as np
import pytest
from src.feature_engineering import add_technical_indicators, create_features


def test_technical_indicators_generation():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    prices = 100 + np.cumsum(np.random.randn(60))
    df = pd.DataFrame({
        "Date": dates,
        "Close": prices,
        "Open": prices - 0.5,
        "High": prices + 1.0,
        "Low": prices - 1.0,
        "Volume": np.random.randint(10000, 50000, size=60)
    })
    
    df_feat = add_technical_indicators(df)
    
    assert "RSI" in df_feat.columns
    assert "MACD" in df_feat.columns
    assert "BB_Upper" in df_feat.columns
    assert "BB_Lower" in df_feat.columns
    assert not df_feat["RSI"].dropna().empty
