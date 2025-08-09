"""
Ranking Engine Module

This module implements the core ranking algorithm that combines price momentum
and news sentiment to create composite scores for investment decision making.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

from src.data_acquisition.market_data import MarketDataManager, create_market_data_manager
from src.data_acquisition.news_sentiment import NewsAndSentimentManager, create_news_sentiment_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Core ranking engine that combines price momentum and sentiment analysis
    to generate investment rankings for stocks and ETFs.
    """
    
    def __init__(self, 
                 price_weight: float = 0.6,
                 sentiment_weight: float = 0.4,
                 market_data_provider: str = 'yahoo'):
        """
        Initialize the ranking engine
        
        Args:
            price_weight: Weight for price momentum in composite score (0-1)
            sentiment_weight: Weight for sentiment in composite score (0-1)
            market_data_provider: Primary market data provider ('yahoo' or 'alpha_vantage')
        """
        if abs(price_weight + sentiment_weight - 1.0) > 0.001:
            raise ValueError("Price weight and sentiment weight must sum to 1.0")
        
        self.price_weight = price_weight
        self.sentiment_weight = sentiment_weight
        
        # Initialize data managers
        self.market_data_manager = create_market_data_manager(market_data_provider)
        self.news_sentiment_manager = create_news_sentiment_manager()
        
        logger.info(f"Initialized RankingEngine with weights: price={price_weight}, sentiment={sentiment_weight}")
    
    def normalize_scores(self, scores: List[float], method: str = 'minmax') -> List[float]:
        """
        Normalize scores to 0-100 range
        
        Args:
            scores: List of scores to normalize
            method: Normalization method ('minmax' or 'zscore')
            
        Returns:
            List of normalized scores
        """
        if not scores or len(scores) == 0:
            return []
        
        scores_array = np.array(scores)
        
        if method == 'minmax':
            min_score = scores_array.min()
            max_score = scores_array.max()
            
            if max_score == min_score:
                return [50.0] * len(scores)  # All scores are the same
            
            normalized = 100 * (scores_array - min_score) / (max_score - min_score)
            
        elif method == 'zscore':
            mean_score = scores_array.mean()
            std_score = scores_array.std()
            
            if std_score == 0:
                return [50.0] * len(scores)  # All scores are the same
            
            # Z-score normalization, then shift to 0-100 range
            z_scores = (scores_array - mean_score) / std_score
            # Map z-scores to 0-100 (assuming most z-scores fall within -3 to +3)
            normalized = 50 + (z_scores * 50 / 3)
            normalized = np.clip(normalized, 0, 100)
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return normalized.tolist()
    
    def calculate_technical_score(self, price_data: Dict) -> float:
        """
        Calculate technical score based on price momentum
        
        Args:
            price_data: Dictionary with price information
            
        Returns:
            Technical score
        """
        if not price_data or price_data.get('price') is None:
            return 0.0
        
        # Base score from percent change
        percent_change = price_data.get('percent_change', 0.0)
        
        # Additional factors can be added here (RSI, MACD, etc.)
        # For now, we'll use percent change as the primary technical indicator
        
        return percent_change
    
    def calculate_sentiment_score(self, sentiment_data: Dict) -> float:
        """
        Calculate sentiment score from news analysis
        
        Args:
            sentiment_data: Dictionary with sentiment analysis results
            
        Returns:
            Sentiment score
        """
        if not sentiment_data:
            return 0.0
        
        # Base sentiment score (-1 to +1)
        base_sentiment = sentiment_data.get('average_sentiment', 0.0)
        
        # Adjust based on number of headlines (more headlines = more confidence)
        headline_count = sentiment_data.get('headline_count', 0)
        confidence_multiplier = min(1.0, headline_count / 10)  # Max confidence at 10+ headlines
        
        # Adjust based on sentiment consistency
        sentiment_std = sentiment_data.get('sentiment_std', 0.0)
        consistency_bonus = max(0.0, 1.0 - sentiment_std) * 0.1  # Up to 10% bonus for consistency
        
        # Final sentiment score
        adjusted_sentiment = base_sentiment * confidence_multiplier + consistency_bonus
        
        return adjusted_sentiment
    
    def rank_assets(self, 
                   tickers: List[str], 
                   include_details: bool = False) -> pd.DataFrame:
        """
        Rank a list of assets based on price momentum and sentiment
        
        Args:
            tickers: List of stock/ETF symbols to rank
            include_details: Whether to include detailed data in results
            
        Returns:
            DataFrame with ranked assets and scores
        """
        logger.info(f"Starting ranking analysis for {len(tickers)} assets")
        start_time = time.time()
        
        # Fetch market data
        logger.info("Fetching market data...")
        price_data = self.market_data_manager.get_price_data(tickers)
        
        # Fetch sentiment data
        logger.info("Fetching sentiment data...")
        sentiment_data = self.news_sentiment_manager.get_sentiment_for_multiple_tickers(tickers)
        
        # Prepare data for analysis
        analysis_data = {}
        technical_scores = []
        sentiment_scores = []
        
        for ticker in tickers:
            ticker_price_data = price_data.get(ticker, {})
            ticker_sentiment_data = sentiment_data.get(ticker, {})
            
            tech_score = self.calculate_technical_score(ticker_price_data)
            sent_score = self.calculate_sentiment_score(ticker_sentiment_data)
            
            analysis_data[ticker] = {
                'price': ticker_price_data.get('price'),
                'percent_change': ticker_price_data.get('percent_change', 0.0),
                'volume': ticker_price_data.get('volume', 0),
                'technical_score_raw': tech_score,
                'sentiment_score_raw': sent_score,
                'headline_count': ticker_sentiment_data.get('headline_count', 0),
                'sentiment_std': ticker_sentiment_data.get('sentiment_std', 0.0),
                'positive_ratio': ticker_sentiment_data.get('positive_ratio', 0.0),
                'negative_ratio': ticker_sentiment_data.get('negative_ratio', 0.0),
            }
            
            technical_scores.append(tech_score)
            sentiment_scores.append(sent_score)
        
        # Normalize scores
        logger.info("Normalizing scores...")
        normalized_technical = self.normalize_scores(technical_scores, method='minmax')
        normalized_sentiment = self.normalize_scores([s + 1 for s in sentiment_scores], method='minmax')  # Shift sentiment to positive range
        
        # Calculate composite scores
        for i, ticker in enumerate(tickers):
            tech_norm = normalized_technical[i]
            sent_norm = normalized_sentiment[i]
            
            composite_score = (self.price_weight * tech_norm + 
                             self.sentiment_weight * sent_norm)
            
            analysis_data[ticker].update({
                'technical_score': tech_norm,
                'sentiment_score': sent_norm,
                'composite_score': composite_score
            })
        
        # Create DataFrame
        df = pd.DataFrame.from_dict(analysis_data, orient='index')
        df.index.name = 'ticker'
        df = df.reset_index()
        
        # Sort by composite score (descending)
        df = df.sort_values('composite_score', ascending=False)
        df = df.reset_index(drop=True)
        df['rank'] = df.index + 1
        
        # Filter columns based on include_details
        if include_details:
            columns = ['rank', 'ticker', 'composite_score', 'technical_score', 'sentiment_score',
                      'price', 'percent_change', 'volume', 'headline_count', 'positive_ratio', 
                      'negative_ratio', 'sentiment_std']
        else:
            columns = ['rank', 'ticker', 'composite_score', 'technical_score', 'sentiment_score',
                      'price', 'percent_change']
        
        result_df = df[columns].copy()
        
        # Add metadata
        result_df.attrs['analysis_timestamp'] = datetime.now()
        result_df.attrs['price_weight'] = self.price_weight
        result_df.attrs['sentiment_weight'] = self.sentiment_weight
        result_df.attrs['total_assets'] = len(tickers)
        result_df.attrs['analysis_duration'] = time.time() - start_time
        
        logger.info(f"Ranking analysis completed in {result_df.attrs['analysis_duration']:.2f} seconds")
        
        return result_df
    
    def get_top_picks(self, 
                     tickers: List[str], 
                     top_n: int = 5,
                     min_sentiment_headlines: int = 3) -> pd.DataFrame:
        """
        Get top investment picks with filtering criteria
        
        Args:
            tickers: List of stock/ETF symbols to analyze
            top_n: Number of top picks to return
            min_sentiment_headlines: Minimum number of headlines required for inclusion
            
        Returns:
            DataFrame with top picks
        """
        # Get full ranking
        full_ranking = self.rank_assets(tickers, include_details=True)
        
        # Apply filters
        filtered_ranking = full_ranking[
            full_ranking['headline_count'] >= min_sentiment_headlines
        ].copy()
        
        if len(filtered_ranking) == 0:
            logger.warning("No assets met the filtering criteria. Returning unfiltered top picks.")
            filtered_ranking = full_ranking
        
        # Return top N
        top_picks = filtered_ranking.head(top_n).copy()
        
        # Add recommendation strength
        top_picks['recommendation'] = top_picks['composite_score'].apply(
            lambda x: 'Strong Buy' if x >= 80 else 
                     'Buy' if x >= 65 else 
                     'Hold' if x >= 50 else 
                     'Weak Hold' if x >= 35 else 'Avoid'
        )
        
        return top_picks
    
    def analyze_single_asset(self, ticker: str) -> Dict:
        """
        Perform detailed analysis of a single asset
        
        Args:
            ticker: Stock/ETF symbol
            
        Returns:
            Dictionary with detailed analysis
        """
        ranking_df = self.rank_assets([ticker], include_details=True)
        
        if len(ranking_df) == 0:
            return {'error': f'No data available for {ticker}'}
        
        asset_data = ranking_df.iloc[0].to_dict()
        
        # Add historical context
        try:
            historical_data = self.market_data_manager.get_historical_data(ticker, period="3mo")
            if not historical_data.empty:
                asset_data['historical_volatility'] = historical_data['Close'].pct_change().std() * 100
                asset_data['avg_volume_3m'] = historical_data['Volume'].mean()
                asset_data['price_trend_3m'] = ((historical_data['Close'].iloc[-1] - 
                                               historical_data['Close'].iloc[0]) / 
                                              historical_data['Close'].iloc[0]) * 100
        except Exception as e:
            logger.warning(f"Could not fetch historical data for {ticker}: {e}")
        
        # Add stock info
        try:
            stock_info = self.market_data_manager.get_stock_info(ticker)
            asset_data.update(stock_info)
        except Exception as e:
            logger.warning(f"Could not fetch stock info for {ticker}: {e}")
        
        return asset_data
    
    def update_weights(self, price_weight: float, sentiment_weight: float):
        """
        Update the weights for price and sentiment components
        
        Args:
            price_weight: New weight for price momentum
            sentiment_weight: New weight for sentiment
        """
        if abs(price_weight + sentiment_weight - 1.0) > 0.001:
            raise ValueError("Price weight and sentiment weight must sum to 1.0")
        
        self.price_weight = price_weight
        self.sentiment_weight = sentiment_weight
        
        logger.info(f"Updated weights: price={price_weight}, sentiment={sentiment_weight}")


# Factory function for easy instantiation
def create_ranking_engine(price_weight: float = 0.6, 
                         sentiment_weight: float = 0.4,
                         market_data_provider: str = 'yahoo') -> RankingEngine:
    """
    Factory function to create a RankingEngine instance
    
    Args:
        price_weight: Weight for price momentum (default 0.6)
        sentiment_weight: Weight for sentiment (default 0.4)
        market_data_provider: Market data provider to use
        
    Returns:
        RankingEngine instance
    """
    return RankingEngine(price_weight, sentiment_weight, market_data_provider)


if __name__ == "__main__":
    # Example usage
    engine = create_ranking_engine()
    
    # Test with popular stocks and ETFs
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'SPY', 'QQQ', 'IWM']
    
    print("Running ranking analysis...")
    rankings = engine.rank_assets(test_tickers, include_details=True)
    
    print("\n--- Top Investment Rankings ---")
    print(rankings[['rank', 'ticker', 'composite_score', 'technical_score', 
                   'sentiment_score', 'percent_change']].to_string(index=False))
    
    print(f"\nAnalysis completed at: {rankings.attrs['analysis_timestamp']}")
    print(f"Total analysis time: {rankings.attrs['analysis_duration']:.2f} seconds")
    
    # Get top picks
    print("\n--- Top 3 Picks ---")
    top_picks = engine.get_top_picks(test_tickers, top_n=3)
    print(top_picks[['ticker', 'composite_score', 'recommendation', 'percent_change']].to_string(index=False))
