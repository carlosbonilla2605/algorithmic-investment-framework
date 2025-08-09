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
        """Get database URL from environment variables"""
        
        # Try PostgreSQL first (recommended for production)
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        if all([db_host, db_name, db_user, db_password]):
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Fallback to SQLite for development
        db_path = os.getenv('SQLITE_DB_PATH', '../data/investment_framework.db')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        logger.warning("PostgreSQL credentials not found, using SQLite for development")
        return f"sqlite:///{db_path}"
    
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
    
    def get_or_create_security(self, symbol: str, **kwargs) -> Optional[Security]:
        """Get existing security or create new one"""
        security = self.get_security(symbol)
        if security:
            return security
        return self.add_security(symbol, **kwargs)
    
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
        """Get latest price data"""
        with self.get_session() as session:
            return DatabaseQueries.get_latest_prices(session, symbols, limit_days)
    
    def get_recent_news(self, symbol: str, days: int = 7):
        """Get recent news for symbol"""
        with self.get_session() as session:
            return DatabaseQueries.get_recent_news(session, symbol, days)
    
    def get_latest_rankings(self, analysis_date: datetime = None, limit: int = 50):
        """Get latest rankings"""
        with self.get_session() as session:
            return DatabaseQueries.get_latest_rankings(session, analysis_date, limit)
    
    def get_trade_history(self, symbol: str = None, days: int = 30):
        """Get trade history"""
        with self.get_session() as session:
            return DatabaseQueries.get_trade_history(session, symbol, days)
    
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
                
                stats.update({
                    'latest_price_date': latest_price_date[0] if latest_price_date else None,
                    'latest_news_date': latest_news_date[0] if latest_news_date else None,
                    'latest_ranking_date': latest_ranking_date[0] if latest_ranking_date else None
                })
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}


# Factory function for easy instantiation
def create_database_manager(database_url: str = None, echo: bool = False) -> DatabaseManager:
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
