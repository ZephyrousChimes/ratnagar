import os
import requests
import polars as pl
from datetime import datetime
from birkeland import config
from birkeland.utils.logging import get_logger


logger = get_logger(__name__)


def fetch_1min_ohlcv(ticker: str, range_days="5d") -> pl.DataFrame:

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range={range_days}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://finance.yahoo.com/",
        "Connection": "keep-alive"
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()

    if 'chart' not in data or 'result' not in data['chart'] or data['chart']['result'] is None:
        raise ValueError(f"No data returned for ticker \"{ticker}\": {data['chart']['error']}")

    result = data['chart']['result'][0]
    timestamps = result['timestamp']
    ohlcv = result['indicators']['quote'][0]

    dt_index = [datetime.fromtimestamp(ts) for ts in timestamps]

    df = pl.DataFrame({
        "datetime": dt_index,
        "open": ohlcv['open'],
        "high": ohlcv['high'],
        "low": ohlcv['low'],
        "close": ohlcv['close'],
        "volume": ohlcv['volume']
    })

    logger.info(f"Fetched {len(df)} rows of 1-min OHLCV for {ticker}")
    return df


def save_1min_incremental(ticker: str, new_data: pl.DataFrame):
    dir_path = os.path.join(config.DATA_DIR, "price", "1min")
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{ticker}.parquet")

    if os.path.exists(file_path):
        existing_data = pl.read_parquet(file_path)
        combined_data = pl.concat([existing_data, new_data]).unique(subset=['datetime'])
        logger.info(f"Existing data loaded for {ticker}: {len(existing_data)} rows")
    else:
        combined_data = new_data
        logger.info(f"No existing data found for {ticker}. Creating new file.")

    combined_data = combined_data.sort('datetime')
    combined_data.write_parquet(file_path)
    logger.info(f"Saved {len(combined_data)} total rows of 1-min data for {ticker} to {file_path}")


def fetch_and_store_1min_ohlcv(tickers=None):
    tickers = tickers or config.DEFAULT_TICKERS
    for ticker in tickers:
        try:
            logger.info(f"Fetching 1-min OHLCV for {ticker}")
            df = fetch_1min_ohlcv(ticker)
            save_1min_incremental(ticker, df)
        except Exception as e:
            logger.error(f"Failed to fetch/store data for {ticker}: {e}")


if __name__ == "__main__":
    fetch_and_store_1min_ohlcv()
