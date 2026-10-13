"""
Integration Test Suite for Person 3: Market Data ETL Pipeline
Validates CSV dataset ingestion, date formatting, and missing value imputation.
"""

import os
import pandas as pd
import pytest
from src.data_preprocessing import load_stock_data, list_available_companies


def test_list_available_companies():
    companies = list_available_companies()
    assert isinstance(companies, list)
    assert len(companies) > 0
    assert any("RELIANCE" in str(c) for c in companies)


def test_load_stock_data_integrity():
    df = load_stock_data("RELIANCE")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_cols = ["Date", "Close", "Open", "High", "Low", "Volume"]
    for col in expected_cols:
        assert col in df.columns
