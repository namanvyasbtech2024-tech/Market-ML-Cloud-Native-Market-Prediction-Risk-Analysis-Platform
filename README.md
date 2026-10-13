# Market ML: Financial Market Prediction, Quantitative Analytics & Cloud Observability Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Container-Docker_MultiStage-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![AWS](https://img.shields.io/badge/Cloud-AWS_EC2-FF9900.svg?logo=amazon-aws&logoColor=white)](https://aws.amazon.com)
[![Machine Learning](https://img.shields.io/badge/ML-XGBoost_%7C_RandomForest-blue.svg)](https://scikit-learn.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)

An enterprise-grade, full-stack financial market analytics platform featuring multi-model machine learning price forecasting (XGBoost, Random Forest), technical indicator analysis, algorithmic strategy backtesting, Markowitz portfolio optimization, and live sentiment analysis across 45+ NSE bluechip equities.

---

## 👥 Engineering Team & Core Responsibilities

| Contributor | Engineering Role | Core Deliverables |
|---|---|---|
| **Naman Vyas** (`namanvyasbtech2024-tech`) | **Cloud Platform & Frontend UI Lead (Person 1)** | • Responsive Single-Page Dark Theme UI (`app/templates/index.html`)<br>• Plotly Charting Engine & Client-Server Controllers (`script_v52.js`)<br>• Design System & Stylesheets (`style_v3.css`)<br>• Multi-Stage Dockerfile & Production Docker Compose (Port 80/8000)<br>• ASGI Server Entrypoint (`main.py`) |
| **amakshita0506-dot** (`amakshita0506-dot`) | **Data & Machine Learning Lead (Person 2)** | • Dual-Paradigm ML Modeling: Regression & Directional Classification<br>• Gradient-boosted decision trees (XGBoost) & Random Forest ensembles<br>• Technical Indicator Feature Engineering (RSI, MACD, Bollinger Bands, SMA)<br>• Algorithmic Trading Strategy Backtester & 1-Year Price Forecaster<br>• Global Feature Importance (SHAP-compatible) |
| **Anushka200610** (`Anushka200610`) | **Cloud Pipelines & API Integration Lead (Person 3)** | • Automated Market Data Ingestion & ETL Pipelines (`data/*.csv`)<br>• Live Quote Synchronization via yfinance (`src/live_data.py`)<br>• VADER Financial News & Reddit Market Sentiment Scraper<br>• REST API Routing Layer (`/api/stocks`, `/api/data`, `/api/train`)<br>• Portfolio Allocation & Optimization Endpoints |

---

## 🖥️ Platform Navigation & Feature Suite

The dashboard is structured into 6 institutional tabs:

1. **Analysis Tab**:
   * Interactive candlestick and line charts with timeframe filters (`1M`, `3M`, `6M`, `1Y`, `Max`).
   * Dynamic overlays: Bollinger Bands (\(20\sigma\)), SMA 50/200, Volume histograms.
   * Real-time metrics ribbon: Current Price, Day Change, 52W High, Volume, API status.
2. **Model Evaluation Tab**:
   * Side-by-side performance comparison: XGBoost vs. Random Forest vs. Linear Regression.
   * Directional Accuracy (\(DA\)), Mean Absolute Error (\(MAE\)), \(RMSE\), \(R^2\).
   * Feature importance rankings identifying predictive technical signals.
3. **Strategy Backtest Tab**:
   * Quantitative trading strategy simulation testing moving average crossovers.
   * Comparative equity curves against Buy & Hold benchmark with Sharpe ratio and Drawdown.
4. **1-Year Forecast Tab**:
   * Forward-looking ML trajectory projecting future trading days with confidence bounds.
5. **Portfolio Tab**:
   * Capital management, Markowitz AI optimization, and 1,000-path Net Worth Monte Carlo simulations.
6. **News & Sentiment Tab**:
   * VADER financial sentiment scoring on live market headlines and retail investor commentary.

---

## 🚀 Quickstart & Local Development

```bash
git clone https://github.com/namanvyasbtech2024-tech/Risk-Citadel-Multi-Sector-Concentration-Analytics-and-Black-Swan-Simulation-Platform.git
cd Risk-Citadel-Multi-Sector-Concentration-Analytics-and-Black-Swan-Simulation-Platform

# Install dependencies
pip install -r requirements.txt

# Run the server
python3 main.py
```
Open your browser at **`http://localhost:8000`** (or `http://localhost:8001`).

---

## 🐳 Docker & Cloud Deployment (AWS EC2)

```bash
sudo docker compose up -d --build
```
Access directly at **`http://<YOUR_EC2_PUBLIC_IP>`** (Standard HTTP port 80).
