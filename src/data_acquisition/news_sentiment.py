"""
News and Sentiment Analysis Module

This module handles fetching financial news and performing sentiment analysis
using VADER sentiment analyzer and web scraping from FinViz.
"""

import os
import time
import logging
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download VADER lexicon if not already present
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    logger.info("Downloading VADER lexicon...")
    nltk.download('vader_lexicon')


class NewsProvider:
    """Base class for news providers"""
    
    def __init__(self):
        self.rate_limit_delay = 0.2
    
    def get_news_headlines(self, ticker: str) -> List[str]:
        """Get news headlines for a ticker"""
        raise NotImplementedError
    
    def get_news_with_sentiment(self, ticker: str) -> List[Dict]:
        """Get news with sentiment scores"""
        raise NotImplementedError


class FinVizNewsProvider(NewsProvider):
    """FinViz news provider using web scraping"""
    
    def __init__(self):
        super().__init__()
        self.base_url = 'https://finviz.com/quote.ashx'
        self.headers = {
            'user-agent': 'algorithmic-investment-framework/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.rate_limit_delay = 1.0  # Be respectful to FinViz servers
    
    def get_news_headlines(self, ticker: str) -> List[str]:
        """
        Scrapes news headlines for a given ticker from FinViz.
        
        Args:
            ticker: Stock/ETF symbol
            
        Returns:
            List of news headlines
        """
        url = f'{self.base_url}?t={ticker.upper()}'
        # Supports TASK-007: Scrape FinViz headlines with respectful rate limits and error handling
        headlines = []
        
        try:
            logger.info(f"Fetching news for {ticker} from FinViz")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_table = soup.find(id='news-table')
            
            if news_table:
                news_rows = news_table.find_all('tr')
                
                for row in news_rows:
                    link_element = row.find('a')
                    if link_element and link_element.text:
                        headline = link_element.text.strip()
                        if headline and len(headline) > 10:  # Filter out very short headlines
                            headlines.append(headline)
                
                logger.info(f"Found {len(headlines)} headlines for {ticker}")
            else:
                logger.warning(f"No news table found for {ticker}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching news for {ticker}: {e}")
        except Exception as e:
            logger.error(f"Error parsing news for {ticker}: {e}")
        
        return headlines[:20]  # Limit to top 20 headlines
    
    def get_news_with_timestamps(self, ticker: str) -> List[Dict]:
        """
        Get news headlines with timestamps from FinViz
        
        Args:
            ticker: Stock/ETF symbol
            
        Returns:
            List of dictionaries with headline and timestamp
        """
        url = f'{self.base_url}?t={ticker.upper()}'
        news_items = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_table = soup.find(id='news-table')
            
            if news_table:
                news_rows = news_table.find_all('tr')
                
                for row in news_rows:
                    # Try to extract timestamp
                    time_cell = row.find('td', {'class': 'news-date-time'})
                    if not time_cell:
                        time_cell = row.find('td')  # First cell often contains time
                    
                    # Extract headline
                    link_element = row.find('a')
                    
                    if link_element and link_element.text:
                        headline = link_element.text.strip()
                        timestamp = time_cell.text.strip() if time_cell else "Unknown"
                        
                        if headline and len(headline) > 10:
                            news_items.append({
                                'headline': headline,
                                'timestamp': timestamp,
                                'source': 'FinViz'
                            })
                
        except Exception as e:
            logger.error(f"Error fetching timestamped news for {ticker}: {e}")
        
        return news_items[:15]


class SentimentAnalyzer:
    """Sentiment analysis using VADER and other methods"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Financial sentiment keywords for enhancement
        self.positive_finance_words = {
            'bullish', 'gains', 'surge', 'rally', 'outperform', 'beat', 'exceed',
            'strong', 'growth', 'profit', 'revenue', 'upgrade', 'buy', 'positive',
            'momentum', 'breakthrough', 'expansion', 'acquisition', 'dividend'
        }
        
        self.negative_finance_words = {
            'bearish', 'losses', 'decline', 'crash', 'underperform', 'miss', 'below',
            'weak', 'loss', 'deficit', 'downgrade', 'sell', 'negative', 'concern',
            'lawsuit', 'investigation', 'bankruptcy', 'recession', 'volatility'
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a text using VADER with financial context
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        # Get VADER scores
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # Enhance with financial keywords
        text_lower = text.lower()
        financial_boost = 0.0
        
        # Count positive and negative financial terms
        pos_count = sum(1 for word in self.positive_finance_words if word in text_lower)
        neg_count = sum(1 for word in self.negative_finance_words if word in text_lower)
        
        # Apply financial context boost
        if pos_count > neg_count:
            financial_boost = min(0.2, (pos_count - neg_count) * 0.1)
        elif neg_count > pos_count:
            financial_boost = max(-0.2, (pos_count - neg_count) * 0.1)
        
        # Adjust compound score
        enhanced_compound = vader_scores['compound'] + financial_boost
        enhanced_compound = max(-1.0, min(1.0, enhanced_compound))  # Clamp to [-1, 1]
        
        return {
            'compound': enhanced_compound,
            'positive': vader_scores['pos'],
            'neutral': vader_scores['neu'],
            'negative': vader_scores['neg'],
            'financial_boost': financial_boost,
            'original_compound': vader_scores['compound']
        }
    
    def analyze_headlines(self, headlines: List[str]) -> Dict[str, float]:
        """
        Analyze sentiment of multiple headlines and return aggregated scores
        
        Args:
            headlines: List of news headlines
            
        Returns:
            Dictionary with aggregated sentiment metrics
        """
        if not headlines:
            # Supports TASK-008: VADER-based sentiment with headline counts
            return {
                'average_sentiment': 0.0,
                'sentiment_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'headline_count': 0
            }
        
        sentiments = [self.analyze_sentiment(headline) for headline in headlines]
        compound_scores = [s['compound'] for s in sentiments]
        
        # Calculate aggregated metrics
        avg_sentiment = sum(compound_scores) / len(compound_scores)
        
        # Count sentiment categories (using threshold of 0.05)
        positive_count = sum(1 for score in compound_scores if score > 0.05)
        negative_count = sum(1 for score in compound_scores if score < -0.05)
        neutral_count = len(compound_scores) - positive_count - negative_count
        
        total_count = len(compound_scores)
        
        return {
            'average_sentiment': avg_sentiment,
            'sentiment_score': avg_sentiment,  # Alias for compatibility
            'positive_ratio': positive_count / total_count,
            'negative_ratio': negative_count / total_count,
            'neutral_ratio': neutral_count / total_count,
            'headline_count': total_count,
            'sentiment_std': self._calculate_std(compound_scores),
            'max_sentiment': max(compound_scores),
            'min_sentiment': min(compound_scores)
        }
    
    def _calculate_std(self, scores: List[float]) -> float:
        """Calculate standard deviation of sentiment scores"""
        if len(scores) <= 1:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return variance ** 0.5


class NewsAndSentimentManager:
    """Manager class for coordinating news fetching and sentiment analysis"""
    
    def __init__(self, news_provider: NewsProvider = None):
        """
        Initialize with news provider and sentiment analyzer
        
        Args:
            news_provider: Instance of a news provider (defaults to FinViz)
        """
        self.news_provider = news_provider or FinVizNewsProvider()
        self.sentiment_analyzer = SentimentAnalyzer()
        logger.info("Initialized NewsAndSentimentManager")
    
    def get_sentiment_for_ticker(self, ticker: str) -> Dict:
        """
        Get news headlines and sentiment analysis for a ticker
        
        Args:
            ticker: Stock/ETF symbol
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            headlines = self.news_provider.get_news_headlines(ticker)
            # Per-headline sentiments for persistence and UI
            headline_sentiments = [
                self.sentiment_analyzer.analyze_sentiment(h)
                for h in headlines
            ] if headlines else []

            sentiment_results = self.sentiment_analyzer.analyze_headlines(headlines)

            return {
                'ticker': ticker,
                'headlines': headlines,
                'headline_sentiments': headline_sentiments,
                **sentiment_results
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment for {ticker}: {e}")
            return {
                'ticker': ticker,
                'headlines': [],
                'average_sentiment': 0.0,
                'sentiment_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'headline_count': 0
            }
    
    def get_sentiment_for_multiple_tickers(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Get sentiment analysis for multiple tickers
        
        Args:
            tickers: List of stock/ETF symbols
            
        Returns:
            Dictionary mapping tickers to sentiment results
        """
        results = {}
        
        for ticker in tickers:
            logger.info(f"Processing sentiment for {ticker}")
            results[ticker] = self.get_sentiment_for_ticker(ticker)
            
            # Rate limiting
            time.sleep(self.news_provider.rate_limit_delay)
        
        return results


# Factory function for easy instantiation
def create_news_sentiment_manager() -> NewsAndSentimentManager:
    """
    Factory function to create a NewsAndSentimentManager instance
    
    Returns:
        NewsAndSentimentManager instance
    """
    return NewsAndSentimentManager()


if __name__ == "__main__":
    # Example usage
    manager = create_news_sentiment_manager()
    
    test_tickers = ['AAPL', 'TSLA', 'NVDA']
    
    print("Fetching news sentiment...")
    sentiment_data = manager.get_sentiment_for_multiple_tickers(test_tickers)
    
    for ticker, data in sentiment_data.items():
        print(f"\n{ticker}:")
        print(f"  Headlines found: {data['headline_count']}")
        print(f"  Average sentiment: {data['average_sentiment']:.3f}")
        print(f"  Positive ratio: {data['positive_ratio']:.2%}")
        print(f"  Recent headlines:")
        for headline in data['headlines'][:3]:
            print(f"    - {headline}")
