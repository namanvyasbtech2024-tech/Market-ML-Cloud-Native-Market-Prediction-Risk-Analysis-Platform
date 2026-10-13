# Person 2 Technical Architecture: Quantitative Algorithms & Machine Learning Engines

**Author**: amakshita0506-dot (Data & Machine Learning Lead)  
**GitHub**: `amakshita0506-dot`  
**Platform**: Market ML — Financial Market Prediction & Concentration Analytics  

---

## 1. Executive Summary
Person 2 designs and implements the core mathematical, econometric, and machine learning components of **Market ML**. This includes multi-model training pipelines (XGBoost, Random Forest, Linear Regression), directional classification engines, automated feature engineering, algorithmic backtesting, and forward-looking Monte Carlo forecasting.

---

## 2. Machine Learning Model Suite (`src/model_training.py`)

### 1. Dual Paradigm Modeling
* **Regression Modeling**: Predicts exact continuous next-day closing prices (\(\hat{y}_{t+1}\)) to compute pricing residuals and error distributions.
* **Directional Classification**: Predicts binary next-day market direction (\(\text{Sign}(P_{t+1} - P_t)\)) to power algorithmic trade triggers:
  $$\text{Directional Accuracy} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\left(\text{sign}(y_{\text{true}, i}) == \text{sign}(y_{\text{pred}, i})\right)$$

### 2. Supported Algorithms
* **XGBoost (Extreme Gradient Boosting)**: Gradient-boosted decision trees optimized with regularization (\(L_1, L_2\)) to handle noisy financial time-series.
* **Random Forest**: Ensemble of 100 bagging estimators providing high out-of-bag stability and non-linear feature interaction capture.
* **Linear / Ridge Regression**: Baseline econometric models for benchmark comparison.

### 3. Model Evaluation Diagnostics
* Continuous Metrics: Mean Absolute Error (\(MAE\)), Root Mean Squared Error (\(RMSE\)), Coefficient of Determination (\(R^2\)).
* Binary Directional Metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.

---

## 3. Algorithmic Feature Engineering (`src/feature_engineering.py`)
Extracts predictive alpha signals from raw price and volume sequences:
* **Relative Strength Index (RSI)**: 14-period momentum oscillator detecting overbought (>70) and oversold (<30) conditions.
* **Moving Average Convergence Divergence (MACD)**: 12-period fast EMA minus 26-period slow EMA, with a 9-period signal EMA.
* **Bollinger Bands**: 20-period SMA flanked by \(\pm 2\sigma\) rolling standard deviation bands.
* **Volume Weighted Average Price (VWAP)** and rolling volatility estimators.

---

## 4. Backtesting & Forward Forecasting (`src/backtest.py`, `app/forecast_routes.py`)
* **Historical Backtester**: Replays trading signals across historical market data, accounting for position transitions, equity curves, maximum drawdown, and annualized Sharpe ratios.
* **1-Year Price Forecaster**: Generates forward-looking 252-day predictive paths with upper and lower volatility confidence intervals.
