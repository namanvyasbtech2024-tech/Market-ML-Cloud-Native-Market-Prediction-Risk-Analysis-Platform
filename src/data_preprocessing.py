import os
from functools import lru_cache

import pandas as pd


# Determine the project root directory (works in Streamlit Cloud and local)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)  # Go up from src/ to project root

# Define data folder paths (compatible with Streamlit Cloud)
NIFTY50_FOLDER = os.path.join(_project_root, "data")
NSE_STOCKS_FOLDER = os.path.join(_project_root, "data")


@lru_cache(maxsize=32)
def list_nifty50_companies():
    """List available Nifty 50 company tickers from the data directory."""
    if not os.path.isdir(NIFTY50_FOLDER):
        raise FileNotFoundError(f"Data folder not found: {NIFTY50_FOLDER}")

    files = [f for f in os.listdir(NIFTY50_FOLDER) if f.endswith(".csv")]
    tickers = sorted([os.path.splitext(f)[0] for f in files])
    return tickers


@lru_cache(maxsize=32)
def list_available_companies():
    """List all available company tickers from both Nifty50 and NSE datasets.
    Falls back to NIFTY 50 default list if local data folders are not found (e.g., in Streamlit Cloud)."""
    tickers = set()

    # Add Nifty50 stocks
    if os.path.isdir(NIFTY50_FOLDER):
        try:
            files = [f for f in os.listdir(NIFTY50_FOLDER) if f.endswith(".csv")]
            nifty_tickers = [os.path.splitext(f)[0] for f in files]
            tickers.update(nifty_tickers)
        except Exception:
            pass  # Silently continue if unable to list

    # Add NSE stocks (remove .NS suffix)
    if os.path.isdir(NSE_STOCKS_FOLDER):
        try:
            files = [f for f in os.listdir(NSE_STOCKS_FOLDER) if f.endswith(".NS.csv")]
            nse_tickers = [os.path.splitext(os.path.splitext(f)[0])[0] for f in files]
            tickers.update(nse_tickers)
        except Exception:
            pass  # Silently continue if unable to list

    # If no local data found, return NIFTY 50 default tickers (for Streamlit Cloud compatibility)
    if not tickers:
        tickers = {
            "ADANIPORTS", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV",
            "BAJFINANCE", "BHARTIARTL", "BPCL", "BRITANNIA", "CIPLA",
            "COALINDIA", "DRREDDY", "EICHERMOT", "GAIL", "GRASIM",
            "HCLTECH", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
            "INDUSINDBK", "INFY", "IOC", "ITC", "JSWSTEEL",
            "KOTAKBANK", "LT", "MARUTI", "MM", "NESTLEIND",
            "NTPC", "ONGC", "POWERGRID", "RELIANCE", "SBIN",
            "SHREECEM", "SUNPHARMA", "TATAMOTORS", "TATASTEEL", "TCS",
            "TECHM", "TITAN", "ULTRACEMCO", "UPL", "VEDL", "WIPRO", "ZEEL"
        }

    return sorted(list(tickers))


@lru_cache(maxsize=32)
def load_stock_data(ticker: str, data_dir: str = None) -> pd.DataFrame:
    """Load stock historical data for a given ticker from the local CSV dataset.
    Falls back to yfinance if local data is not available (e.g., in Streamlit Cloud)."""
    
    # Try to load from local CSV
    if data_dir is None:
        path = None
        # First try Nifty50 folder
        nifty_path = os.path.join(NIFTY50_FOLDER, f"{ticker}.csv")
        if os.path.isfile(nifty_path):
            path = nifty_path
        else:
            # Try NSE stocks folder with .NS.csv extension
            nse_path = os.path.join(NSE_STOCKS_FOLDER, f"{ticker}.NS.csv")
            if os.path.isfile(nse_path):
                path = nse_path

        # If found, load from CSV
        if path:
            try:
                df = pd.read_csv(path)
                # Standardize column names
                df.columns = [c.strip() for c in df.columns]

                # convert date and ensure sorting
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"])
                    df = df.sort_values("Date").reset_index(drop=True)
                else:
                    raise ValueError(f"CSV for {ticker} does not contain a 'Date' column")

                # ensure numeric columns
                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                return df
            except Exception as e:
                # If CSV loading fails, fall back to yfinance below
                pass

    # Fallback: Use yfinance for live data (works in Streamlit Cloud)
    try:
        import yfinance as yf
        # Append .NS suffix for Indian stocks if not already present
        symbol = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        data = yf.download(symbol, progress=False)
        
        # Handle case where yfinance returns None or empty
        if data is None or data.empty:
            raise ValueError(f"No data returned from yfinance for {symbol}")
        
        # Reset index to make Date a column
        if isinstance(data.columns, pd.MultiIndex):
            # If MultiIndex, flatten it
            data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in data.columns.values]
        
        df = data.reset_index()
        
        # Ensure column names are strings and strip whitespace
        df.columns = [str(c).strip() for c in df.columns]
        
        # Standardize column names (yfinance uses 'Date' or 'Datetime')
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        if "Date" not in df.columns:
            raise ValueError(f"Could not find Date column in yfinance data for {ticker}")
        
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        
        return df
    except Exception as e:
        raise FileNotFoundError(f"Could not load stock data for '{ticker}' from local CSV or yfinance: {e}")


def filter_by_date(df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    """Filter the data between start_date and end_date inclusive."""
    out = df.copy()
    if start_date is not None:
        out = out[out["Date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        out = out[out["Date"] <= pd.to_datetime(end_date)]
    return out.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_nifty_index() -> pd.DataFrame:
    """Build a simple NIFTY index proxy using the mean of all constituent closing prices."""
    tickers = list_nifty50_companies()
    frames = []
    for ticker in tickers:
        try:
            df = load_stock_data(ticker)[["Date", "Close"]].rename(columns={"Close": ticker})
            frames.append(df)
        except Exception:
            continue

    if not frames:
        raise RuntimeError("No stock data found to calculate NIFTY index")

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="Date", how="outer")

    merged = merged.sort_values("Date").reset_index(drop=True)
    merged = merged.ffill().bfill()

    merged["NIFTY_INDEX"] = merged[[t for t in tickers if t in merged.columns]].mean(axis=1)
    return merged[["Date", "NIFTY_INDEX"]]
