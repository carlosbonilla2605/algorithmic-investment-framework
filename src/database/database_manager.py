"""
Database Manager Module

This module provides database connection management, initialization,
and common operations for the investment framework.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from .models import (
    Base, Security, PriceData, NewsArticle, SecurityNewsLink,
    ArticleSentiment, RankingResult, TradeRecord, Portfolio,
    Position, SystemLog, DatabaseQueries, create_additional_indexes
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection and operations manager
    """
    
    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection URL (if None, reads from env)
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url or self._get_database_url()
        self.echo = echo
        self.engine = None
        self.SessionLocal = None
        
        self._initialize_database()
    
    def _get_database_url(self) -> str:
        """Get the database URL from environment or use default SQLite path"""
        # Use environment variable if set
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            logger.info(f"Using database URL from environment: {database_url}")
            return database_url
            
        # Default to SQLite database in data directory
        db_path = os.path.join(os.getcwd(), 'data', 'investment_framework.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db_url = f'sqlite:///{db_path}'
        logger.info(f"Using default SQLite database at: {db_path}")
        return db_url
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=self.echo,
                pool_pre_ping=True,  # Validate connections before use
                pool_recycle=3600    # Recycle connections every hour
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create additional indexes
            create_additional_indexes(self.engine)
            
            logger.info(f"Database initialized successfully: {self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    # Security operations
    def add_security(self, symbol: str, name: str = None, **kwargs) -> Optional[Security]:
        """Add a new security to the database"""
        try:
            with self.get_session() as session:
                # Check if security already exists
                existing = session.query(Security).filter(Security.symbol == symbol).first()
                if existing:
                    logger.info(f"Security {symbol} already exists")
                    return existing
                
                security = Security(
                    symbol=symbol.upper(),
                    name=name,
                    **kwargs
                )
                
                session.add(security)
                session.commit()
                session.refresh(security)
                
                logger.info(f"Added security: {symbol}")
                return security
                
        except Exception as e:
            logger.error(f"Error adding security {symbol}: {e}")
            return None
    
    def get_security(self, symbol: str) -> Optional[Security]:
        """Get security by symbol"""
        try:
            with self.get_session() as session:
                return session.query(Security).filter(Security.symbol == symbol.upper()).first()
        except Exception as e:
            logger.error(f"Error getting security {symbol}: {e}")
            return None
    
    def get_or_create_security(self, symbol: str, session: Session = None, **kwargs) -> Optional[Security]:
        """Get existing security or create new one"""
        try:
            if session:
                # Direct session operations
                security = session.query(Security).filter(Security.symbol == symbol.upper()).first()
                if security:
                    return security
                
                security = Security(symbol=symbol.upper(), **kwargs)
                session.add(security)
                session.flush()  # Get the ID without committing
                return security
            else:
                # Use existing methods with their own sessions
                security = self.get_security(symbol)
                if security:
                    return security
                return self.add_security(symbol, **kwargs)
        except Exception as e:
            logger.error(f"Error in get_or_create_security for {symbol}: {e}")
            return None
    
    # Price data operations
    def add_price_data(self, symbol: str, date: datetime, 
                      open_price: float, high: float, low: float, 
                      close: float, volume: int, **kwargs) -> bool:
        """Add price data for a security"""
        try:
            with self.get_session() as session:
                security = self.get_or_create_security(symbol)
                if not security:
                    return False
                
                # Check if price data already exists
                existing = session.query(PriceData).filter(
                    PriceData.security_id == security.id,
                    PriceData.date == date
                ).first()
                
                if existing:
                    # Update existing record
                    existing.open_price = open_price
                    existing.high_price = high
                    existing.low_price = low
                    existing.close_price = close
                    existing.volume = volume
                    for key, value in kwargs.items():
                        setattr(existing, key, value)
                else:
                    # Create new record
                    price_data = PriceData(
                        security_id=security.id,
                        date=date,
                        open_price=open_price,
                        high_price=high,
                        low_price=low,
                        close_price=close,
                        volume=volume,
                        **kwargs
                    )
                    session.add(price_data)
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding price data for {symbol}: {e}")
            return False
    
    def bulk_add_price_data(self, price_records: List[Dict]) -> int:
        """Bulk add price data records"""
        added_count = 0
        
        try:
            with self.get_session() as session:
                for record in price_records:
                    symbol = record.get('symbol')
                    security = self.get_or_create_security(symbol)
                    
                    if not security:
                        continue
                    
                    # Check if already exists
                    existing = session.query(PriceData).filter(
                        PriceData.security_id == security.id,
                        PriceData.date == record['date']
                    ).first()
                    
                    if not existing:
                        price_data = PriceData(
                            security_id=security.id,
                            date=record['date'],
                            open_price=record.get('open_price'),
                            high_price=record.get('high_price'),
                            low_price=record.get('low_price'),
                            close_price=record['close_price'],
                            volume=record.get('volume'),
                            data_source=record.get('data_source', 'unknown')
                        )
                        session.add(price_data)
                        added_count += 1
                
                session.commit()
                logger.info(f"Bulk added {added_count} price data records")
                
        except Exception as e:
            logger.error(f"Error bulk adding price data: {e}")
        
        return added_count
    
    # News and sentiment operations
    def add_news_article(self, headline: str, url: str = None, content: str = None,
                        source: str = None, published_at: datetime = None,
                        related_symbols: List[str] = None) -> Optional[NewsArticle]:
        """Add a news article"""
        try:
            with self.get_session() as session:
                # Check if article already exists (by headline or URL)
                existing = None
                if url:
                    existing = session.query(NewsArticle).filter(NewsArticle.url == url).first()
                
                if not existing:
                    existing = session.query(NewsArticle).filter(NewsArticle.headline == headline).first()
                
                if existing:
                    return existing
                
                article = NewsArticle(
                    headline=headline,
                    url=url,
                    content=content,
                    source=source,
                    published_at=published_at or datetime.utcnow()
                )
                
                session.add(article)
                session.flush()  # Get the ID
                
                # Link to securities
                if related_symbols:
                    for symbol in related_symbols:
                        security = self.get_or_create_security(symbol)
                        if security:
                            link = SecurityNewsLink(
                                security_id=security.id,
                                article_id=article.id
                            )
                            session.add(link)
                
                session.commit()
                session.refresh(article)
                
                logger.info(f"Added news article: {headline[:50]}...")
                return article
                
        except Exception as e:
            logger.error(f"Error adding news article: {e}")
            return None
    
    def add_sentiment_analysis(self, article_id: int, sentiment_model: str,
                              compound_score: float, **kwargs) -> bool:
        """Add sentiment analysis for an article"""
        try:
            with self.get_session() as session:
                sentiment = ArticleSentiment(
                    article_id=article_id,
                    sentiment_model=sentiment_model,
                    compound_score=compound_score,
                    **kwargs
                )
                
                session.add(sentiment)
                session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding sentiment analysis: {e}")
            return False
    
    # Ranking operations
    def save_ranking_results(self, ranking_df, algorithm_version: str = "1.0") -> bool:
        """Save ranking results to database"""
        try:
            with self.get_session() as session:
                analysis_date = datetime.utcnow()
                
                for _, row in ranking_df.iterrows():
                    symbol = row['ticker']
                    security = self.get_or_create_security(symbol)
                    
                    if not security:
                        continue
                    
                    ranking = RankingResult(
                        security_id=security.id,
                        analysis_date=analysis_date,
                        rank=row.get('rank'),
                        composite_score=row.get('composite_score'),
                        technical_score=row.get('technical_score'),
                        sentiment_score=row.get('sentiment_score'),
                        price_change_1d=row.get('percent_change'),
                        news_count=row.get('headline_count'),
                        positive_news_ratio=row.get('positive_ratio'),
                        algorithm_version=algorithm_version,
                        price_weight=ranking_df.attrs.get('price_weight'),
                        sentiment_weight=ranking_df.attrs.get('sentiment_weight')
                    )
                    
                    session.add(ranking)
                
                session.commit()
                logger.info(f"Saved ranking results for {len(ranking_df)} securities")
                return True
                
        except Exception as e:
            logger.error(f"Error saving ranking results: {e}")
            return False
    
    # Trade operations
    def record_trade(self, symbol: str, trade_type: str, quantity: int,
                    price: float, order_id: str = None, **kwargs) -> bool:
        """Record a trade execution"""
        try:
            with self.get_session() as session:
                security = self.get_or_create_security(symbol)
                if not security:
                    return False
                
                trade = TradeRecord(
                    security_id=security.id,
                    order_id=order_id,
                    trade_type=trade_type,
                    quantity=quantity,
                    price=price,
                    total_value=quantity * price,
                    trade_date=datetime.utcnow(),
                    **kwargs
                )
                
                session.add(trade)
                session.commit()
                
                logger.info(f"Recorded trade: {trade_type} {quantity} {symbol} @ ${price:.2f}")
                return True
                
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            return False
    
    # Portfolio operations
    def update_portfolio_snapshot(self, total_value: float, cash_balance: float,
                                 positions_value: float, **kwargs) -> bool:
        """Update portfolio snapshot"""
        try:
            with self.get_session() as session:
                snapshot = Portfolio(
                    snapshot_date=datetime.utcnow(),
                    total_value=total_value,
                    cash_balance=cash_balance,
                    positions_value=positions_value,
                    **kwargs
                )
                
                session.add(snapshot)
                session.commit()
                
                logger.info(f"Updated portfolio snapshot: ${total_value:,.2f}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating portfolio snapshot: {e}")
            return False
    
    # Logging operations
    def log_system_event(self, level: str, module: str, message: str,
                        details: str = None, error_traceback: str = None):
        """Log system events"""
        try:
            with self.get_session() as session:
                log_entry = SystemLog(
                    level=level,
                    module=module,
                    message=message,
                    details=details,
                    error_traceback=error_traceback
                )
                
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            # Don't log errors in logging to avoid recursion
            pass
    
    # Query operations using the DatabaseQueries class
    def get_latest_prices(self, symbols: List[str], limit_days: int = 5):
        """Get latest price data as plain dicts to avoid detached ORM issues"""
        with self.get_session() as session:
            rows = DatabaseQueries.get_latest_prices(session, symbols, limit_days)
            results: List[Dict[str, Any]] = []
            for row in rows:
                # Row is (PriceData, Security)
                price_obj, sec_obj = None, None
                if hasattr(row, 'PriceData') and hasattr(row, 'Security'):
                    price_obj = row.PriceData
                    sec_obj = row.Security
                elif isinstance(row, (tuple, list)) and len(row) >= 2:
                    price_obj, sec_obj = row[0], row[1]
                else:
                    continue
                try:
                    results.append({
                        'symbol': getattr(sec_obj, 'symbol', None),
                        'date': getattr(price_obj, 'date', None),
                        'open_price': float(price_obj.open_price) if getattr(price_obj, 'open_price', None) is not None else None,
                        'high_price': float(price_obj.high_price) if getattr(price_obj, 'high_price', None) is not None else None,
                        'low_price': float(price_obj.low_price) if getattr(price_obj, 'low_price', None) is not None else None,
                        'close_price': float(price_obj.close_price) if getattr(price_obj, 'close_price', None) is not None else None,
                        'volume': int(price_obj.volume) if getattr(price_obj, 'volume', None) is not None else None,
                        'data_source': getattr(price_obj, 'data_source', None)
                    })
                except Exception:
                    # Skip problematic rows
                    continue
            return results
    
    def get_recent_news(self, symbol: str, days: int = 7):
        """Get recent news for symbol as plain dicts to avoid detached ORM issues"""
        with self.get_session() as session:
            rows = DatabaseQueries.get_recent_news(session, symbol, days)
            results: List[Dict[str, Any]] = []
            for row in rows:
                article_obj, sentiment_obj = None, None
                # Rows can be tuple-like (NewsArticle, ArticleSentiment)
                if hasattr(row, 'NewsArticle') and hasattr(row, 'ArticleSentiment'):
                    article_obj = row.NewsArticle
                    sentiment_obj = row.ArticleSentiment
                elif isinstance(row, (tuple, list)) and len(row) >= 2:
                    article_obj, sentiment_obj = row[0], row[1]
                elif isinstance(row, (tuple, list)) and len(row) == 1:
                    article_obj = row[0]
                else:
                    article_obj = row if not isinstance(row, (tuple, list)) else None
                if article_obj is None:
                    continue
                try:
                    results.append({
                        'published_at': getattr(article_obj, 'published_at', None),
                        'headline': getattr(article_obj, 'headline', None),
                        'source': getattr(article_obj, 'source', None),
                        'compound_score': float(getattr(sentiment_obj, 'compound_score', 0.0)) if sentiment_obj is not None else None,
                        'positive_score': float(getattr(sentiment_obj, 'positive_score', 0.0)) if sentiment_obj is not None else None,
                        'negative_score': float(getattr(sentiment_obj, 'negative_score', 0.0)) if sentiment_obj is not None else None,
                        'neutral_score': float(getattr(sentiment_obj, 'neutral_score', 0.0)) if sentiment_obj is not None else None,
                    })
                except Exception:
                    continue
            return results
    
    def get_latest_rankings(self, analysis_date: Optional[datetime] = None, limit: int = 50):
        """Get latest rankings as plain dicts to avoid detached ORM issues"""
        with self.get_session() as session:
            rows = DatabaseQueries.get_latest_rankings(session, analysis_date, limit)
            results: List[Dict[str, Any]] = []
            for row in rows:
                # Row is (RankingResult, Security)
                rank_obj, sec_obj = None, None
                if hasattr(row, 'RankingResult') and hasattr(row, 'Security'):
                    rank_obj = row.RankingResult
                    sec_obj = row.Security
                elif isinstance(row, (tuple, list)) and len(row) >= 2:
                    rank_obj, sec_obj = row[0], row[1]
                else:
                    continue
                try:
                    results.append({
                        'symbol': getattr(sec_obj, 'symbol', None),
                        'analysis_date': getattr(rank_obj, 'analysis_date', None),
                        'rank': getattr(rank_obj, 'rank', None),
                        'composite_score': float(rank_obj.composite_score) if getattr(rank_obj, 'composite_score', None) is not None else None,
                        'technical_score': float(rank_obj.technical_score) if getattr(rank_obj, 'technical_score', None) is not None else None,
                        'sentiment_score': float(rank_obj.sentiment_score) if getattr(rank_obj, 'sentiment_score', None) is not None else None,
                        'price_change_1d': float(rank_obj.price_change_1d) if getattr(rank_obj, 'price_change_1d', None) is not None else None,
                        'news_count': getattr(rank_obj, 'news_count', None),
                        'positive_news_ratio': float(rank_obj.positive_news_ratio) if getattr(rank_obj, 'positive_news_ratio', None) is not None else None,
                        'algorithm_version': getattr(rank_obj, 'algorithm_version', None),
                        'price_weight': float(rank_obj.price_weight) if getattr(rank_obj, 'price_weight', None) is not None else None,
                        'sentiment_weight': float(rank_obj.sentiment_weight) if getattr(rank_obj, 'sentiment_weight', None) is not None else None,
                    })
                except Exception:
                    continue
            return results
    
    def get_trade_history(self, symbol: Optional[str] = None, days: int = 30):
        """Get trade history as plain dicts to avoid detached ORM issues"""
        with self.get_session() as session:
            rows = DatabaseQueries.get_trade_history(session, symbol, days)
            results: List[Dict[str, Any]] = []
            for row in rows:
                trade_obj, sec_obj = None, None
                if hasattr(row, 'TradeRecord') and hasattr(row, 'Security'):
                    trade_obj = row.TradeRecord
                    sec_obj = row.Security
                elif isinstance(row, (tuple, list)) and len(row) >= 2:
                    trade_obj, sec_obj = row[0], row[1]
                else:
                    continue
                try:
                    results.append({
                        'date': getattr(trade_obj, 'trade_date', None),
                        'type': getattr(trade_obj, 'trade_type', None),
                        'quantity': int(getattr(trade_obj, 'quantity', 0) or 0),
                        'price': float(getattr(trade_obj, 'price', 0) or 0),
                        'total_value': float(getattr(trade_obj, 'total_value', 0) or 0),
                        'symbol': getattr(sec_obj, 'symbol', None)
                    })
                except Exception:
                    continue
            return results
    
    def get_portfolio_performance(self, days: int = 30):
        """Get portfolio performance"""
        with self.get_session() as session:
            return DatabaseQueries.get_portfolio_performance(session, days)
    
    # Maintenance operations
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old data to maintain database size"""
        try:
            with self.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                # Clean old system logs
                old_logs = session.query(SystemLog).filter(
                    SystemLog.timestamp < cutoff_date
                ).delete()
                
                # Clean old portfolio snapshots (keep monthly snapshots)
                # This is more complex - you might want to keep daily snapshots for recent data
                # and monthly snapshots for older data
                
                session.commit()
                logger.info(f"Cleaned up {old_logs} old log entries")
                
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_session() as session:
                stats = {
                    'securities_count': session.query(Security).count(),
                    'price_records_count': session.query(PriceData).count(),
                    'news_articles_count': session.query(NewsArticle).count(),
                    'ranking_results_count': session.query(RankingResult).count(),
                    'trade_records_count': session.query(TradeRecord).count(),
                    'portfolio_snapshots_count': session.query(Portfolio).count()
                }
                
                # Get latest dates
                latest_price_date = session.query(PriceData.date).order_by(PriceData.date.desc()).first()
                latest_news_date = session.query(NewsArticle.published_at).order_by(NewsArticle.published_at.desc()).first()
                latest_ranking_date = session.query(RankingResult.analysis_date).order_by(RankingResult.analysis_date.desc()).first()
                
                stats['latest_price_date'] = latest_price_date[0] if latest_price_date else None
                stats['latest_news_date'] = latest_news_date[0] if latest_news_date else None
                stats['latest_ranking_date'] = latest_ranking_date[0] if latest_ranking_date else None
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}


# Factory function for easy instantiation
def create_database_manager(database_url: Optional[str] = None, echo: bool = False) -> DatabaseManager:
    """
    Factory function to create a DatabaseManager instance
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        DatabaseManager instance
    """
    return DatabaseManager(database_url, echo)


if __name__ == "__main__":
    # Example usage and testing
    db_manager = create_database_manager()
    
    # Test connection
    if db_manager.test_connection():
        print("✅ Database connection successful")
        
        # Get database stats
        stats = db_manager.get_database_stats()
        print("\n📊 Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Database connection failed")
