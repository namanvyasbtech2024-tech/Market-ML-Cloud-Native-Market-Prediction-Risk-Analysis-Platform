from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from src.data_preprocessing import load_stock_data

forecast_router = APIRouter(prefix="/api")

@forecast_router.get("/forecast/{ticker}")
async def get_1yr_forecast(ticker: str):
    try:
        df = load_stock_data(ticker)
        if df.empty or len(df) < 252:
            raise HTTPException(status_code=400, detail="Not enough data for 1-year forecast")

        df = df.sort_index()
        closes = df['Close'].values
        last_price = closes[-1]
        
        # 1. Monte Carlo Simulation (Drift & Volatility)
        # Use last 2 years for historical volatility
        returns = df['Close'].pct_change().dropna()[-504:]
        mu = returns.mean()
        sigma = returns.std()
        
        days_ahead = 252
        num_simulations = 1000
        
        # Calculate daily drift
        drift = mu - (0.5 * sigma**2)
        
        # Generate random shocks
        np.random.seed(42)
        Z = np.random.standard_normal((days_ahead, num_simulations))
        daily_returns = np.exp(drift + sigma * Z)
        
        # Calculate price paths
        price_paths = np.zeros_like(daily_returns)
        price_paths[0] = last_price
        for t in range(1, days_ahead):
            price_paths[t] = price_paths[t - 1] * daily_returns[t]
            
        # Extract percentiles
        mc_best = np.percentile(price_paths, 95, axis=1)
        mc_q75 = np.percentile(price_paths, 75, axis=1)
        mc_q25 = np.percentile(price_paths, 25, axis=1)
        mc_worst = np.percentile(price_paths, 5, axis=1)
        mc_expected = np.mean(price_paths, axis=1)
        
        # Force start at last_price
        mc_best[0] = last_price
        mc_q75[0] = last_price
        mc_q25[0] = last_price
        mc_worst[0] = last_price
        mc_expected[0] = last_price

        # 2. AI Long-Term Trend (Polynomial Time Regression)
        # We model the general macro trend of the stock over the last 3 years
        # and project it forward 1 year.
        trend_df = df.tail(756).copy() # Last 3 years
        X_train = np.arange(len(trend_df)).reshape(-1, 1)
        y_train = trend_df['Close'].values
        
        # Polynomial regression degree 2 for macro curve
        ai_model = make_pipeline(PolynomialFeatures(degree=2), Ridge(alpha=1.0))
        ai_model.fit(X_train, y_train)
        
        # Predict the next 252 days
        X_future = np.arange(len(trend_df), len(trend_df) + days_ahead).reshape(-1, 1)
        ai_raw_trend = ai_model.predict(X_future)
        
        # Smoothly anchor the AI trend to the last actual price to avoid a visual "jump"
        offset = last_price - ai_raw_trend[0]
        ai_trend = ai_raw_trend + offset

        # Generate future dates (skip weekends)
        last_date = pd.to_datetime(df.index[-1] if hasattr(df.index, 'date') and 'Date' not in df.columns else df['Date'].iloc[-1])
        future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=days_ahead)
        future_dates_str = future_dates.strftime('%Y-%m-%d').tolist()

        hist_df = df.tail(90)
        if 'Date' in hist_df.columns:
            hist_dates = hist_df['Date'].astype(str).tolist()
        else:
            hist_dates = hist_df.index.strftime('%Y-%m-%d').tolist()
        hist_prices = hist_df['Close'].tolist()

        return {
            "status": "success",
            "hist_dates": hist_dates,
            "hist_prices": hist_prices,
            "dates": future_dates_str,
            "last_price": float(last_price),
            "monte_carlo": {
                "best": mc_best.tolist(),
                "q75": mc_q75.tolist(),
                "q25": mc_q25.tolist(),
                "expected": mc_expected.tolist(),
                "worst": mc_worst.tolist()
            },
            "ai_trend": ai_trend.tolist()
        }

    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
