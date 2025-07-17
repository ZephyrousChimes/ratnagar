import os
import pandas as pd
import yfinance as yf
from birkeland import config
from birkeland.utils.logging import get_logger


logger = get_logger(__name__)


def fetch_daily_ohlcv(ticker: str, period: str = "max") -> pd.DataFrame:
    logger.info(f"Fetching daily OHLCV for {ticker}, period: {period}")
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(period=period)

    if df.empty:
        logger.warning(f"No data returned for {ticker}")
        return df

    df['dividends'] = ticker_obj.dividends.reindex(df.index, fill_value=0)
    df['splits'] = ticker_obj.splits.reindex(df.index, fill_value=0)

    logger.info(f"Fetched {len(df)} daily rows for {ticker}")
    return df


def save_ohlcv_to_parquet(ticker: str, df: pd.DataFrame) -> None:
    if df.empty:
        logger.warning(f"Skipping save: No data to store for {ticker}")
        return

    dir_path = os.path.join(config.DATA_DIR, "price", "daily")
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{ticker}.parquet")
    df.to_parquet(file_path)
    logger.info(f"Saved {len(df)} daily OHLCV rows for {ticker} to {file_path}")


def fetch_and_store_daily_ohlcv(tickers: list[str] = None, period: str = "max") -> None:
    tickers = tickers or config.DEFAULT_TICKERS

    if len(tickers) == 0:
        logger.error(f"No tickers provided to fetch")

    for ticker in tickers:
        try:
            df = fetch_daily_ohlcv(ticker)
            save_ohlcv_to_parquet(ticker, df)
        except Exception as e:
            logger.error(f"Failed to fetch/store daily OHLCV for {ticker}: {e}")


if __name__ == "__main__":
    fetch_and_store_daily_ohlcv()
