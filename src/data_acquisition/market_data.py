"""
Market Data Acquisition Module

This module handles fetching market data from various APIs including
Alpha Vantage, Polygon.io, and Yahoo Finance.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Base class for market data providers"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = None
        self.rate_limit_delay = 0.1
    
    def get_price_data(self, tickers: List[str]) -> Dict:
        """Get price data for a list of tickers"""
        raise NotImplementedError
    
    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Get historical data for a ticker"""
        raise NotImplementedError


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider using yfinance"""
    
    def __init__(self):
        super().__init__()
        self.rate_limit_delay = 0.1
    
    def get_price_data(self, tickers: List[str]) -> Dict:
        """
        Fetches recent price change data for a list of tickers.
        
        Args:
            tickers: List of stock/ETF symbols
            
        Returns:
            Dictionary with ticker data including price and percent change
        """
    # Supports TASK-005: Yahoo as primary provider
    # Supports TASK-019/020: Logging of provider activity and errors
        price_data = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                
                if not hist.empty and len(hist) > 1:
                    prev_close = hist['Close'].iloc[-2]
                    current_close = hist['Close'].iloc[-1]
                    percent_change = ((current_close - prev_close) / prev_close) * 100
                    
                    price_data[ticker] = {
                        'price': current_close,
                        'percent_change': percent_change,
                        'volume': hist['Volume'].iloc[-1],
                        'timestamp': hist.index[-1]
                    }
                    logger.info(f"Fetched data for {ticker}: {percent_change:.2f}% change")
                else:
                    price_data[ticker] = {
                        'price': None,
                        'percent_change': 0.0,
                        'volume': 0,
                        'timestamp': None
                    }
                    logger.warning(f"No data available for {ticker}")
                    
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
                price_data[ticker] = {
                    'price': None,
                    'percent_change': 0.0,
                    'volume': 0,
                    'timestamp': None
                }
            
            time.sleep(self.rate_limit_delay)
        
        return price_data
    
    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """
        Get historical data for a ticker
        
        Args:
            ticker: Stock/ETF symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame with historical OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_stock_info(self, ticker: str) -> Dict:
        """Get basic stock information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', None),
                'dividend_yield': info.get('dividendYield', None)
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return {'name': ticker, 'sector': 'Unknown', 'industry': 'Unknown'}


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage data provider"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls per minute
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
    
    def get_daily_data(self, ticker: str) -> Dict:
        """Get daily time series data from Alpha Vantage"""
        if not self.api_key:
            return {}
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'apikey': self.api_key,
            'outputsize': 'compact'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                latest_date = max(time_series.keys())
                prev_date = sorted(time_series.keys())[-2]
                
                latest_close = float(time_series[latest_date]['4. close'])
                prev_close = float(time_series[prev_date]['4. close'])
                percent_change = ((latest_close - prev_close) / prev_close) * 100
                
                return {
                    'price': latest_close,
                    'percent_change': percent_change,
                    'volume': int(time_series[latest_date]['5. volume']),
                    'timestamp': latest_date
                }
            else:
                logger.error(f"Alpha Vantage API error for {ticker}: {data}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {ticker}: {e}")
            return {}
    
    def get_price_data(self, tickers: List[str]) -> Dict:
        """Get price data using Alpha Vantage API"""
        price_data = {}
        
        for ticker in tickers:
            data = self.get_daily_data(ticker)
            if data:
                price_data[ticker] = data
            else:
                price_data[ticker] = {
                    'price': None,
                    'percent_change': 0.0,
                    'volume': 0,
                    'timestamp': None
                }
            time.sleep(self.rate_limit_delay)
        
        return price_data


class MarketDataManager:
    """Manager class for coordinating multiple data providers"""
    
    def __init__(self, primary_provider: str = 'yahoo'):
        """
        Initialize with a primary data provider
        
        Args:
            primary_provider: 'yahoo' or 'alpha_vantage'
        """
        self.providers = {
            'yahoo': YahooFinanceProvider(),
            'alpha_vantage': AlphaVantageProvider()
        }

        self.primary_provider = primary_provider
        if primary_provider not in self.providers:
            raise ValueError(f"Unknown provider: {primary_provider}")

        logger.info(f"Initialized MarketDataManager with primary provider: {primary_provider}")
        # Supports TASK-006: Log which provider is used; provider is configurable
    
    def get_price_data(self, tickers: List[str], fallback: bool = True) -> Dict:
        """
        Get price data with fallback to secondary provider
        
        Args:
            tickers: List of stock/ETF symbols
            fallback: Whether to use fallback provider if primary fails
            
        Returns:
            Dictionary with price data for all tickers
        """
        logger.info(f"Fetching price data for {len(tickers)} tickers using {self.primary_provider}")
        
        # Try primary provider
        try:
            data = self.providers[self.primary_provider].get_price_data(tickers)
            
            # Check if we got valid data for most tickers
            valid_data_count = sum(1 for ticker_data in data.values() 
                                 if ticker_data.get('price') is not None)
            
            if valid_data_count >= len(tickers) * 0.8:  # 80% success rate
                logger.info(f"Successfully fetched data for {valid_data_count}/{len(tickers)} tickers")
                return data
            elif fallback:
                logger.warning(f"Primary provider only returned {valid_data_count}/{len(tickers)} valid results. Trying fallback...")
                
        except Exception as e:
            logger.error(f"Primary provider failed: {e}")
            if not fallback:
                raise
        
        # Try fallback provider (Yahoo Finance)
        if fallback and self.primary_provider != 'yahoo':
            try:
                return self.providers['yahoo'].get_price_data(tickers)
            except Exception as e:
                logger.error(f"Fallback provider also failed: {e}")
                raise
        
        # If all else fails, return empty data structure
        return {ticker: {'price': None, 'percent_change': 0.0, 'volume': 0, 'timestamp': None} 
                for ticker in tickers}
    
    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Get historical data using Yahoo Finance provider"""
        return self.providers['yahoo'].get_historical_data(ticker, period)
    
    def get_stock_info(self, ticker: str) -> Dict:
        """Get stock information using Yahoo Finance provider"""
        return self.providers['yahoo'].get_stock_info(ticker)


# Factory function for easy instantiation
def create_market_data_manager(provider: str = 'yahoo') -> MarketDataManager:
    """
    Factory function to create a MarketDataManager instance
    
    Args:
        provider: Primary data provider ('yahoo' or 'alpha_vantage')
        
    Returns:
        MarketDataManager instance
    """
    return MarketDataManager(provider)


if __name__ == "__main__":
    # Example usage
    manager = create_market_data_manager('yahoo')
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print("Fetching price data...")
    price_data = manager.get_price_data(test_tickers)
    
    for ticker, data in price_data.items():
        if data['price']:
            print(f"{ticker}: ${data['price']:.2f} ({data['percent_change']:+.2f}%)")
        else:
            print(f"{ticker}: No data available")
