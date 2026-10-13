# Person 3 Technical Architecture: Cloud Data Pipelines, Sentiment Scrapers & REST API Layer

**Author**: Anushka200610 (Data Pipelines & Client-Cloud Integration Lead)  
**GitHub**: `Anushka200610`  
**Platform**: Market ML — Financial Market Prediction & Concentration Analytics  

---

## 1. Executive Summary
Person 3 is responsible for the automated data ingestion pipelines, real-time market synchronization, alternative data sentiment scrapers, and the asynchronous REST API routing layer that connects the cloud back-end to the browser UI.

---

## 2. Market Data Ingestion & ETL Pipelines (`src/data_preprocessing.py`, `data/`)
* **Multi-Asset Ingestion**: Automated ingestion and synchronization of 45+ National Stock Exchange (NSE) bluechip equities (e.g., RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, ADANIPORTS).
* **Data Cleaning & Normalization**: Automated handling of non-trading holiday gaps, price splits, stock dividends, and forward-filling missing bars.
* **Persistent Cache Management**: Local pre-computed metrics cache (`cache/*_metrics.json`) ensuring instantaneous page loads without redundant recalculations.

---

## 3. Alternative Data & Sentiment Analysis (`src/sentiment_analysis.py`, `src/live_data.py`)
* **Live Market Feeds**: Integration with yfinance for real-time live quotes, 52-week extremes, market capitalization, and daily volume.
* **VADER Financial Sentiment Scraper**: Analyzes incoming financial news headlines and social investor sentiment (Reddit / StockTwits) to produce continuous polarity scores (\([-1.0, +1.0]\)).
* **Sentiment Aggregator**: Normalizes scores into categorized signals (Bullish, Neutral, Bearish) presented on the **News & Sentiment Tab**.

---

## 4. Asynchronous REST API Routing Layer (`app/api_routes.py`, `app/portfolio_routes.py`)
* `/api/stocks`: Returns the list of all available active NSE assets.
* `/api/profile/{ticker}`: Serves corporate overview, sector classification, and financial fundamentals.
* `/api/data/{ticker}`: Delivers time-series price history and technical indicators for Plotly chart rendering.
* `/api/train/{ticker}`: Asynchronously triggers model training (XGBoost, Random Forest) and delivers performance metrics.
* `/api/backtest`: Executes strategy simulation with customized trading thresholds.
* `/api/portfolio/optimize`: Serves Markowitz portfolio weights, discrete integer share lots, and forward net worth trajectories.
