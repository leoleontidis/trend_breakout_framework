import os
import pandas as pd
import yfinance as yf

def load_price_data(symbol, interval="1d", start="2010-01-01", end="2025-12-31"):
    folder = f"data/{interval}"
    os.makedirs(folder, exist_ok=True)

    path = f"{folder}/{symbol}.csv"

    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Date"])
        df = df.set_index("Date")
        print(f"[LOADER] - Loaded {symbol} from {path}")
    else:
        print(f"[DOWNLOADER] - Downloading {symbol} from Yahoo Finance...")
        try:
            df = yf.download(symbol, start=start, end=end, interval=interval)
            if df.empty:
                raise ValueError(f"No data found for {symbol} from Yahoo.")

            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df = df.reset_index()
            df.to_csv(path, index=False)
            print(f"[DOWNLOADER] - Saved {symbol} to {path}")

            df = df.set_index("Date")
        except Exception as e:
            print(f"[ERROR] - Failed to download {symbol}: {e}")
            raise

    for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna()

    return df