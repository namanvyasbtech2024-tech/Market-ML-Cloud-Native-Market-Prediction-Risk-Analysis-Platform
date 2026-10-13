"""
Unit Test Suite for Person 2: Model Explainability & Feature Importance
Validates SHAP-compatible tree feature importance ranking algorithms.
"""

import numpy as np
import pytest
from src.explainability import get_global_feature_importance


def test_feature_importance_synthetic():
    class DummyTreeModel:
        def __init__(self):
            self.feature_importances_ = np.array([0.5, 0.3, 0.2])
    
    model = DummyTreeModel()
    feature_names = ["RSI", "MACD", "Volume"]
    
    importance_df = get_global_feature_importance(model, feature_names)
    
    assert "Feature" in importance_df.columns
    assert "Importance" in importance_df.columns
    assert importance_df.iloc[0]["Feature"] == "RSI"
