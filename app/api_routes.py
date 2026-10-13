from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from src.data_preprocessing import list_available_companies, load_stock_data
from src.model_training import train_regression_models
from src.feature_engineering import create_features, add_technical_indicators
from src.live_data import live_news_data
from src.explainability import get_global_feature_importance
from src.backtest import Backtester

router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Market ML API is online"}


@router.get("/stocks", response_model=List[str])
async def get_stocks():
    try:
        companies = list_available_companies()
        if companies and isinstance(companies[0], dict):
            return [c.get('Symbol', '') for c in companies]
        return companies
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

import yfinance as yf

# Simple in-memory cache for profiles so we don't spam yfinance
profile_cache = {}

@router.get("/profile/{ticker}")
async def get_company_profile(ticker: str):
    try:
        # Add .NS for Indian stocks if missing
        yf_ticker = ticker if ticker.endswith('.NS') else f"{ticker}.NS"
        
        if yf_ticker in profile_cache:
            return profile_cache[yf_ticker]
            
        t = yf.Ticker(yf_ticker)
        info = t.info
        
        def format_mcap(val):
            if not val: return "--"
            if val >= 1e7: return f"₹{val/1e7:,.0f}Cr"
            return f"₹{val:,.0f}"
            
        def format_pct(val):
            if not val: return "--"
            if val > 2: return f"{val:.2f}%"
            return f"{val*100:.2f}%"
            
        def format_float(val):
            if not val: return "--"
            return f"{val:.2f}"
            
        # Fetch Financials
        try:
            qinc = t.quarterly_income_stmt
            if 'Total Revenue' in qinc.index and 'Net Income' in qinc.index:
                # Get the last 5 columns (newest to oldest, so we reverse it)
                dates = qinc.columns[:5][::-1]
                revs = qinc.loc['Total Revenue'].iloc[:5][::-1].tolist()
                profs = qinc.loc['Net Income'].iloc[:5][::-1].tolist()
                
                # Format dates to "Jun '25" etc
                formatted_dates = [d.strftime("%b '%y") for d in dates]
                
                # Calculate % changes for the last quarter
                rev_pct = "--"
                prof_pct = "--"
                if len(revs) >= 2:
                    rev_c = ((revs[-1] - revs[-2]) / abs(revs[-2])) * 100
                    prof_c = ((profs[-1] - profs[-2]) / abs(profs[-2])) * 100
                    rev_pct = f"+{rev_c:.2f}%" if rev_c > 0 else f"{rev_c:.2f}%"
                    prof_pct = f"+{prof_c:.2f}%" if prof_c > 0 else f"{prof_c:.2f}%"
                    
                financials = {
                    "dates": formatted_dates,
                    "revenue": revs,
                    "profit": profs,
                    "revPct": rev_pct,
                    "profPct": prof_pct,
                    "label": formatted_dates[-1] if formatted_dates else "--"
                }
            else:
                financials = None
        except Exception as fe:
            print("Financial fetch error:", fe)
            financials = None
            
        profile = {
            "name": info.get("longName", ticker),
            "about": info.get("longBusinessSummary", "Company description not available."),
            "mktCap": format_mcap(info.get("marketCap")),
            "roe": format_pct(info.get("returnOnEquity")),
            "pe": format_float(info.get("trailingPE")),
            "eps": format_float(info.get("trailingEps")),
            "divYield": format_pct(info.get("dividendYield")),
            "pb": format_float(info.get("priceToBook")),
            "financials": financials
        }
        
        profile_cache[yf_ticker] = profile
        return profile
    except Exception as e:
        print("Error fetching profile:", e)
        # Fallback empty profile
        return {
            "name": ticker,
            "about": "Information currently unavailable due to network or rate limits.",
            "mktCap": "--", "roe": "--", "pe": "--", "eps": "--", "divYield": "--", "pb": "--"
        }

@router.get("/data/{ticker}")
async def get_stock_data(ticker: str):
    try:
        df = load_stock_data(ticker)
        if df.empty: raise HTTPException(status_code=404, detail="No data found")
        df = df.reset_index()
        if "Date" in df.columns: df["Date"] = df["Date"].astype(str)
        df = add_technical_indicators(df); return df[["Date", "Open", "High", "Low", "Close", "Volume", "SMA_20", "BBU_20_2.0", "BBL_20_2.0"]].tail(252).to_dict(orient="records")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/{ticker}")
async def train_model(ticker: str):
    try:
        df = load_stock_data(ticker)
        features = create_features(df).replace([np.inf, -np.inf], np.nan).dropna()
        if features.empty: raise HTTPException(status_code=400, detail="Feature creation failed")
        
        models = train_regression_models(features, target_col="Close")
        results = {}
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        for name, info in models.items():
            y_test = info.get("y_test", [])
            y_pred = info.get("y_pred", [])
            
            # Clean y_pred to prevent NaN/Inf crashing the metrics
            if len(y_pred) > 0:
                y_pred = np.nan_to_num(y_pred, nan=np.nanmean(y_test) if len(y_test)>0 else 0.0, posinf=1e9, neginf=-1e9)
                try:
                    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                    mae = float(mean_absolute_error(y_test, y_pred))
                except Exception as e:
                    print(f"Metrics Error for {name}: {e}")
                    rmse, mae = 0.0, 0.0
            else:
                rmse, mae = 0.0, 0.0
            
            # Extract dates from X_test index using the original features DataFrame
            dates = []
            if "X_test" in info and hasattr(info["X_test"], "index") and "Date" in features.columns:
                dates = features.loc[info["X_test"].index, "Date"].astype(str).tolist()

            dir_acc = 0.0
            if len(y_test) > 1:
                y_t = np.array(y_test)
                y_p = np.array(y_pred)
                actual_diff = np.diff(y_t)
                pred_diff = y_p[1:] - y_t[:-1]
                correct = (np.sign(actual_diff) == np.sign(pred_diff))
                dir_acc = float(np.mean(correct)) * 100.0

            results[name] = {
                "dir_acc": dir_acc,
                "rmse": rmse,
                "mae": mae,
                "r2": float(info.get("r2_score", 0)),
                "dates": dates,
                "y_test": y_test.tolist() if hasattr(y_test, "tolist") else list(y_test),
                "y_pred": y_pred.tolist() if hasattr(y_pred, "tolist") else list(y_pred)
            }
        return {"status": "success", "models": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/correlation/{ticker}")
async def get_news_correlation(ticker: str):
    try:
        # Get historical sentiment
        sentiment_df = live_news_data.get_historical_sentiment(query=ticker, limit=100)
        
        # Get historical stock prices
        df = load_stock_data(ticker)
        # Keep last 90 days
        df = df.tail(90).copy()
        df['Date'] = pd.to_datetime(df['Date'])
        
        if sentiment_df.empty:
            merged = df.copy()
            merged['Sentiment'] = 0.0
        else:
            merged = pd.merge(df, sentiment_df, on='Date', how='left')
            # Fill missing days with 0 (neutral) or forward fill. Let's fill with 0.
            merged['Sentiment'] = merged['Sentiment'].fillna(0.0)
            
            # Smooth the sentiment slightly with a 3-day moving average so it's readable
            merged['Smoothed_Sentiment'] = merged['Sentiment'].rolling(window=3, min_periods=1).mean()
        
        # Convert to dictionary for JSON response
        merged['Date'] = merged['Date'].dt.strftime('%Y-%m-%d')
        return {
            "dates": merged['Date'].tolist(),
            "prices": merged['Close'].tolist(),
            "sentiment": merged['Smoothed_Sentiment'].tolist() if 'Smoothed_Sentiment' in merged else merged['Sentiment'].tolist(),
            "raw_sentiment": merged['Sentiment'].tolist()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def generate_executive_summary(ticker, company_name, recent_news, correlation_df):
    if not recent_news or len(recent_news) == 0:
        return ["Not enough recent news to generate an executive summary."]
    
    import numpy as np
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    
    # 1. Overall Sentiment Trend
    avg_score = np.mean([n['Sentiment_Score'] for n in recent_news])
    sentiment_str = "highly bullish" if avg_score > 0.3 else ("moderately bullish" if avg_score > 0.05 else ("highly bearish" if avg_score < -0.3 else ("moderately bearish" if avg_score < -0.05 else "neutral")))
    
    price_context = ""
    if not correlation_df.empty and len(correlation_df) > 10:
        price_change = ((correlation_df['Close'].iloc[-1] - correlation_df['Close'].iloc[0]) / correlation_df['Close'].iloc[0]) * 100
        direction = "gain" if price_change > 0 else "decline"
        price_context = f" This aligns with a {abs(price_change):.1f}% price {direction} observed over the recent period."
        
    bullet1 = f"Overall market sentiment for {company_name} is currently {sentiment_str} (average score: {avg_score:+.2f}).{price_context}"
    
    # 2. Key Themes (TF-IDF keyword extraction)
    titles = [n['Title'] for n in recent_news]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        custom_stops = list(ENGLISH_STOP_WORDS) + [ticker.lower(), company_name.lower(), 'stock', 'share', 'price', 'nifty', 'sensex', 'market', 'markets', 'nse', 'bse', 'today', 'live', 'news', 'update', 'updates']
        # Split company name to also remove partial matches
        for part in company_name.lower().split():
            custom_stops.append(part)
            
        vectorizer = TfidfVectorizer(stop_words=custom_stops, max_features=10, ngram_range=(1,2))
        X = vectorizer.fit_transform(titles)
        words = np.array(vectorizer.get_feature_names_out())
        scores = X.sum(axis=0).A1
        top_indices = scores.argsort()[-3:][::-1]
        top_keywords = [words[i].title() for i in top_indices if len(words[i]) > 2]
        
        if top_keywords:
            bullet2 = f"Primary narratives and key themes driving current headlines include: {', '.join(top_keywords)}."
        else:
            bullet2 = "News volume is distributed across general market movements without a single dominant keyword theme."
    except Exception as e:
        bullet2 = "News volume is distributed across general market movements without a single dominant keyword theme."
        
    # 3. Most Impactful Headline
    # Find the headline with the maximum absolute sentiment score
    most_impactful = max(recent_news, key=lambda x: abs(x['Sentiment_Score']))
    bullet3 = f"The most notable recent development is: \"{most_impactful['Title']}\" ({most_impactful['Sentiment_Label']})."
    
    return [bullet1, bullet2, bullet3]

@router.get("/news/{ticker}")
async def get_news(ticker: str):
    try:
        news_df = live_news_data.get_live_news(query=ticker, limit=10)
        if news_df.empty:
            return {"news": []}
        
        # Columns from live_data.py are lowercase
        cols = ["title", "published_at", "source", "sentiment_label", "sentiment_score"]
        available_cols = [c for c in cols if c in news_df.columns]
        
        if "published_at" in news_df.columns:
            news_df["published_at"] = news_df["published_at"].astype(str)
            
        # Rename to match frontend expectations
        rename_map = {
            "title": "Title",
            "published_at": "Published At",
            "source": "Source",
            "sentiment_label": "Sentiment_Label",
            "sentiment_score": "Sentiment_Score"
        }
        news_df = news_df.rename(columns=rename_map)
        available_cols = [rename_map.get(c, c) for c in available_cols]
        
        records = news_df[available_cols].to_dict(orient="records")
        
        # Generate AI Summary
        try:
            # We need company_map and correlation data
            company_map = {
                "INFY": "Infosys", "RELIANCE": "Reliance Industries", "TCS": "TCS",
                "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank", "SBIN": "State Bank of India",
                "BHARTIARTL": "Bharti Airtel", "ITC": "ITC", "HINDUNILVR": "Hindustan Unilever",
                "LT": "Larsen & Toubro", "BAJFINANCE": "Bajaj Finance", "AXISBANK": "Axis Bank",
                "KOTAKBANK": "Kotak Mahindra Bank", "MARUTI": "Maruti Suzuki", "TATAMOTORS": "Tata Motors",
                "SUNPHARMA": "Sun Pharma", "TITAN": "Titan Company", "ASIANPAINT": "Asian Paints",
                "BAJAJFINSV": "Bajaj Finserv", "ADANIPORTS": "Adani Ports"
            }
            c_name = company_map.get(ticker, ticker)
            
            # Fast load just to get the price trend
            corr_df = load_stock_data(ticker).tail(30)
            summary_bullets = generate_executive_summary(ticker, c_name, records, corr_df)
        except Exception as ex:
            print("Error generating summary:", ex)
            summary_bullets = []
            
        return {
            "news": records,
            "ai_summary": summary_bullets
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{ticker}")
async def run_backtest(ticker: str):
    try:
        df = load_stock_data(ticker)
        features = create_features(df).replace([np.inf, -np.inf], np.nan).dropna()
        models = train_regression_models(features, target_col="Close")
        
        # Find the best model based on R2 Score
        best_model_name = max(models.keys(), key=lambda k: models[k].get('r2', -float('inf')))
        best_info = models[best_model_name]
        
        y_pred = pd.Series(best_info['y_pred'], index=best_info['X_test'].index)
        
        bt_df = features.loc[y_pred.index].copy()
        
        # Convert continuous price predictions to binary signals (1 = UP, 0 = DOWN)
        # If predicted close > today's open, we predict UP
        signals = (y_pred > bt_df['Open']).astype(int)
        
        bt = Backtester(bt_df, signals.values, transaction_cost=0.001)
        results = bt.run()
        
        # Safe extraction of dates
        if 'Date' in results.columns:
            results['_date_str'] = results['Date'].astype(str)
        else:
            results['_date_str'] = results.index.astype(str)
            
        curve_data = results[['_date_str', 'Strategy_Equity', 'Buy_Hold_Equity']].rename(columns={'_date_str': 'Date'}).to_dict(orient="records")
        
        # Convert DataFrame to dictionary so FastAPI can serialize it
        metrics_df = bt.get_metrics()
        metrics = metrics_df.to_dict()
        
        return {"curve": curve_data, "metrics": metrics}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/explain/{ticker}")
async def get_explainability(ticker: str):
    try:
        df = load_stock_data(ticker)
        features = create_features(df).replace([np.inf, -np.inf], np.nan).dropna()
        models = train_regression_models(features, target_col="Close")
        
        rf_info = models.get('random_forest', list(models.values())[0])
        model = rf_info['model']
        X_test = rf_info['X_test']
        
        importances = get_global_feature_importance(model, X_test)
        top_15_df = importances.head(15)
        imp_col = 'Importance' if 'Importance' in top_15_df.columns else 'SHAP_Importance'
        top_15_dict = dict(zip(top_15_df['Feature'], top_15_df[imp_col]))
        
        return {"importances": top_15_dict}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
