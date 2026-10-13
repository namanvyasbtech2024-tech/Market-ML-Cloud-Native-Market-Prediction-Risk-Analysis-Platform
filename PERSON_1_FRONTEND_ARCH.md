# Person 1 Technical Architecture: Frontend UI, Interactive Visualizations & Cloud Infrastructure

**Author**: Naman Vyas (Cloud Platform & Frontend UI Lead)  
**GitHub**: `namanvyasbtech2024-tech`  
**Platform**: Market ML — Financial Market Prediction & Concentration Analytics  

---

## 1. Executive Summary
Person 1 is responsible for the design, implementation, and cloud deployment of the **Market ML** full-stack institutional web dashboard. The platform provides real-time market technicals, machine learning model diagnostics, forward price forecasting, and portfolio optimization across 45+ NSE bluechip equities.

---

## 2. Core Frontend Architecture
The user interface is built as a high-performance Single Page Application (SPA) with zero external heavyweight JS framework overhead, utilizing native Web APIs and Plotly.js for high-framerate financial charting.

### Dashboard Navigation & Tab Architecture
1. **Analysis Tab**:
   * Multi-timeframe candlestick and line chart engine (`1M`, `3M`, `6M`, `1Y`, `Max`).
   * Dynamic technical overlays: Bollinger Bands (\(20\sigma\)), 50-day and 200-day Simple Moving Averages (SMA), and volume histograms.
   * Real-time KPI Ribbon: Current Price, Daily Change, 52-Week High, Trading Volume, and API Connection health.
2. **Model Evaluation Tab**:
   * Comparative diagnostics for XGBoost, Random Forest, and Linear Regression models.
   * Directional Accuracy metrics (\(DA\)), Mean Absolute Error (\(MAE\)), Root Mean Squared Error (\(RMSE\)), and \(R^2\) coefficient.
   * Confusion matrix and SHAP global feature importance visualizers.
3. **Strategy Backtest Tab**:
   * Quantitative strategy simulator testing moving average crossovers and momentum signals.
   * Equity curves vs. Buy & Hold benchmark with Sharpe ratio and Maximum Drawdown analysis.
4. **1-Year Forecast Tab**:
   * Forward-looking ML trajectory generator simulating 252 future trading days with confidence bounds.
5. **Portfolio Tab**:
   * Capital allocation, Markowitz AI optimization, and 1,000-path Net Worth Monte Carlo simulations.
6. **News & Sentiment Tab**:
   * Live sentiment gauges and aggregated market commentary.

---

## 3. Styling Engine & Design System (`style_v3.css`)
* **Palette**: Dark institutional theme (`#0d1117`, `#161b22`, `#21262d`, `#30363d`).
* **Accents**: Cyan (`#58a6ff`), Positive Alpha Green (`#00e676`), and Risk Red (`#ff5252`).
* **Typography**: Clean monospace and geometric sans-serif for numbers and metric cards.

---

## 4. Cloud Infrastructure & Docker Deployment
* **Containerization**: Multi-stage Python 3.11 Dockerfile with OpenMP runtime.
* **Networking**: Host port `80:8000` mapping for direct browser access at `http://<EC2-IP>` without specifying port numbers.
* **ASGI Server**: Production Uvicorn server running FastAPI with CORS headers and health check monitoring.
