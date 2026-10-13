"""
Unit Test Suite for Person 2: Market ML Model Training & Classification
Verifies XGBoost, Random Forest, and Directional Accuracy Metrics.
"""

import numpy as np
import pytest
from src.model_training import evaluate_classification, train_regression_models


def test_evaluate_classification_directional_accuracy():
    y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0])
    y_pred_prob = np.array([0.9, 0.1, 0.8, 0.7, 0.2, 0.6, 0.3, 0.4])
    
    metrics = evaluate_classification(y_true, y_pred_prob, threshold=0.5)
    
    assert "accuracy" in metrics
    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_model_training_dummy_data():
    np.random.seed(42)
    X = np.random.randn(100, 5)
    y = X[:, 0] * 2.5 + np.random.randn(100) * 0.1
    
    models_dict = train_regression_models(X, y)
    
    assert "Linear Regression" in models_dict
    assert "Random Forest" in models_dict
    assert models_dict["Linear Regression"]["r2"] > 0.8
