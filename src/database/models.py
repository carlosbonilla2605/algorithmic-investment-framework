"""
Database Models for the Algorithmic Investment Framework

This module defines the database schema using SQLAlchemy for storing
market data, news articles, sentiment analysis, and trading records.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, 
    ForeignKey, Index, DECIMAL, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


class Security(Base):
    """
    Securities table storing information about stocks and ETFs
    """
    __tablename__ = 'securities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255))
    exchange = Column(String(10))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(BigInteger)
    security_type = Column(String(20))  # 'stock', 'etf', 'index'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="security")
    news_articles = relationship("SecurityNewsLink", back_populates="security")
    rankings = relationship("RankingResult", back_populates="security")
    trades = relationship("TradeRecord", back_populates="security")
    
    def __repr__(self):
        return f"<Security(symbol='{self.symbol}', name='{self.name}')>"


class PriceData(Base):
    """
    Daily price data for securities
    """
    __tablename__ = 'price_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(Integer, ForeignKey('securities.id'), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(DECIMAL(10, 4))
    high_price = Column(DECIMAL(10, 4))
    low_price = Column(DECIMAL(10, 4))
    close_price = Column(DECIMAL(10, 4), nullable=False)
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(10, 4))
    data_source = Column(String(50))  # 'yahoo', 'alpha_vantage', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security = relationship("Security", back_populates="price_data")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_security_date', 'security_id', 'date'),
    )
    
    def __repr__(self):
        return f"<PriceData(symbol={self.security.symbol}, date={self.date}, close={self.close_price})>"


class NewsArticle(Base):
    """
    News articles table
    """
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    headline = Column(Text, nullable=False)
    url = Column(Text)
    content = Column(Text)
    source = Column(String(100))
    author = Column(String(255))
    published_at = Column(DateTime, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    language = Column(String(10), default='en')
    
    # Relationships
    securities = relationship("SecurityNewsLink", back_populates="article")
    sentiments = relationship("ArticleSentiment", back_populates="article")
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, headline='{self.headline[:50]}...')>"


class SecurityNewsLink(Base):
    """
    Many-to-many link table between securities and news articles
    """
    __tablename__ = 'security_news_link'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(Integer, ForeignKey('securities.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False)
    relevance_score = Column(Float)  # How relevant the article is to this security
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security = relationship("Security", back_populates="news_articles")
    article = relationship("NewsArticle", back_populates="securities")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_security_article', 'security_id', 'article_id'),
    )


class ArticleSentiment(Base):
    """
    Sentiment analysis results for news articles
    """
    __tablename__ = 'article_sentiments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False)
    sentiment_model = Column(String(50))  # 'vader', 'finbert', etc.
    compound_score = Column(Float, nullable=False)
    positive_score = Column(Float)
    negative_score = Column(Float)
    neutral_score = Column(Float)
    confidence_score = Column(Float)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    article = relationship("NewsArticle", back_populates="sentiments")
    
    def __repr__(self):
        return f"<ArticleSentiment(article_id={self.article_id}, compound={self.compound_score})>"


class RankingResult(Base):
    """
    Results from the ranking algorithm
    """
    __tablename__ = 'ranking_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(Integer, ForeignKey('securities.id'), nullable=False)
    analysis_date = Column(DateTime, nullable=False, index=True)
    rank = Column(Integer)
    composite_score = Column(Float, nullable=False)
    technical_score = Column(Float)
    sentiment_score = Column(Float)
    price_change_1d = Column(Float)
    price_change_7d = Column(Float)
    price_change_30d = Column(Float)
    volume_ratio = Column(Float)  # Current volume vs average
    news_count = Column(Integer)
    positive_news_ratio = Column(Float)
    algorithm_version = Column(String(20))
    price_weight = Column(Float)
    sentiment_weight = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security = relationship("Security", back_populates="rankings")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_analysis_date_rank', 'analysis_date', 'rank'),
        Index('idx_security_analysis_date', 'security_id', 'analysis_date'),
    )
    
    def __repr__(self):
        return f"<RankingResult(symbol={self.security.symbol}, rank={self.rank}, score={self.composite_score})>"


class TradeRecord(Base):
    """
    Record of executed trades
    """
    __tablename__ = 'trade_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(Integer, ForeignKey('securities.id'), nullable=False)
    order_id = Column(String(100))  # Broker order ID
    trade_type = Column(String(10), nullable=False)  # 'buy', 'sell'
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 4), nullable=False)
    total_value = Column(DECIMAL(12, 2))
    fees = Column(DECIMAL(10, 2))
    trade_date = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(DateTime)
    order_type = Column(String(20))  # 'market', 'limit', 'stop'
    status = Column(String(20))  # 'filled', 'partial', 'cancelled'
    strategy = Column(String(50))  # Strategy that generated this trade
    ranking_score = Column(Float)  # Score that led to this trade
    stop_loss_price = Column(DECIMAL(10, 4))
    take_profit_price = Column(DECIMAL(10, 4))
    broker = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security = relationship("Security", back_populates="trades")
    
    def __repr__(self):
        return f"<TradeRecord(symbol={self.security.symbol}, type={self.trade_type}, qty={self.quantity})>"


class Portfolio(Base):
    """
    Portfolio snapshots for tracking performance
    """
    __tablename__ = 'portfolio_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    total_value = Column(DECIMAL(15, 2), nullable=False)
    cash_balance = Column(DECIMAL(15, 2))
    positions_value = Column(DECIMAL(15, 2))
    unrealized_pnl = Column(DECIMAL(15, 2))
    realized_pnl_daily = Column(DECIMAL(15, 2))
    realized_pnl_total = Column(DECIMAL(15, 2))
    number_of_positions = Column(Integer)
    largest_position_pct = Column(Float)
    beta = Column(Float)  # Portfolio beta vs market
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Portfolio(date={self.snapshot_date}, value={self.total_value})>"


class Position(Base):
    """
    Current portfolio positions
    """
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(Integer, ForeignKey('securities.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_cost = Column(DECIMAL(10, 4), nullable=False)
    current_price = Column(DECIMAL(10, 4))
    market_value = Column(DECIMAL(12, 2))
    unrealized_pnl = Column(DECIMAL(12, 2))
    unrealized_pnl_pct = Column(Float)
    first_purchase_date = Column(DateTime)
    last_update = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    security = relationship("Security")
    
    def __repr__(self):
        return f"<Position(symbol={self.security.symbol}, qty={self.quantity}, value={self.market_value})>"


class SystemLog(Base):
    """
    System logs for monitoring and debugging
    """
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10))  # 'INFO', 'WARNING', 'ERROR', 'DEBUG'
    module = Column(String(50))
    message = Column(Text)
    details = Column(Text)  # JSON or additional details
    error_traceback = Column(Text)
    
    def __repr__(self):
        return f"<SystemLog(level={self.level}, module={self.module}, time={self.timestamp})>"


# Create indexes for better performance
def create_additional_indexes(engine):
    """Create additional indexes for optimal query performance"""
    from sqlalchemy import text
    
    with engine.connect() as connection:
        # Price data indexes
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_price_data_date_desc 
            ON price_data (date DESC)
        """))
        
        # Create indexes without transaction management (DDL auto-commits)
        # News articles indexes
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_published_desc 
            ON news_articles (published_at DESC)
        """))
        
        # Ranking results indexes
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ranking_score_desc 
            ON ranking_results (composite_score DESC)
        """))
        
        # Trade records indexes
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trades_date_desc 
            ON trade_records (trade_date DESC)
        """))


# Helper functions for common queries
class DatabaseQueries:
    """Common database queries for the investment framework"""
    
    @staticmethod
    def get_latest_prices(session: Session, symbols: list, limit_days: int = 5):
        """Get latest price data for given symbols"""
        return session.query(PriceData, Security).join(Security).filter(
            Security.symbol.in_(symbols),
            PriceData.date >= func.date('now', f'-{limit_days} days')
        ).order_by(PriceData.date.desc()).all()
    
    @staticmethod
    def get_recent_news(session: Session, symbol: str, days: int = 7):
        """Get recent news for a specific symbol"""
        return session.query(NewsArticle, ArticleSentiment).join(
            SecurityNewsLink
        ).join(Security).join(ArticleSentiment).filter(
            Security.symbol == symbol,
            NewsArticle.published_at >= func.date('now', f'-{days} days')
        ).order_by(NewsArticle.published_at.desc()).all()
    
    @staticmethod
    def get_latest_rankings(session: Session, analysis_date: Optional[datetime] = None, limit: int = 50):
        """Get latest ranking results"""
        query = session.query(RankingResult, Security).join(Security)
        
        if analysis_date:
            query = query.filter(RankingResult.analysis_date == analysis_date)
        else:
            # Get the most recent analysis date
            latest_date = session.query(func.max(RankingResult.analysis_date)).scalar()
            if latest_date:
                query = query.filter(RankingResult.analysis_date == latest_date)
        
        return query.order_by(RankingResult.rank).limit(limit).all()
    
    @staticmethod
    def get_trade_history(session: Session, symbol: Optional[str] = None, days: int = 30):
        """Get trade history"""
        query = session.query(TradeRecord, Security).join(Security)
        
        if symbol:
            query = query.filter(Security.symbol == symbol)
        
        query = query.filter(
            TradeRecord.trade_date >= func.date('now', f'-{days} days')
        )
        
        return query.order_by(TradeRecord.trade_date.desc()).all()
    
    @staticmethod
    def get_portfolio_performance(session: Session, days: int = 30):
        """Get portfolio performance over time"""
        return session.query(Portfolio).filter(
            Portfolio.snapshot_date >= func.date('now', f'-{days} days')
        ).order_by(Portfolio.snapshot_date.desc()).all()
