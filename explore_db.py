"""
Script to explore the contents of the database
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import Security, PriceData, NewsArticle, RankingResult, TradeRecord
from datetime import datetime, timedelta

def explore_database():
    # Create database URL for SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'investment_framework.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    database_url = f'sqlite:///{db_path}'
    
    # Create engine and tables
    engine = create_engine(database_url)
    from src.database.models import Base
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check Securities
        securities = session.query(Security).all()
        print("\n=== Securities in Database ===")
        print(f"Total securities: {len(securities)}")
        if securities:
            print("Sample securities:")
            for sec in securities[:5]:
                print(f"- {sec.symbol}: {sec.name} ({sec.security_type})")
        
        # Check Price Data
        price_count = session.query(PriceData).count()
        recent_prices = session.query(PriceData).order_by(PriceData.date.desc()).limit(5).all()
        print("\n=== Price Data ===")
        print(f"Total price records: {price_count}")
        if recent_prices:
            print("Most recent price records:")
            for price in recent_prices:
                print(f"- {price.security.symbol} on {price.date}: ${price.close_price}")
        
        # Check News Articles
        news_count = session.query(NewsArticle).count()
        recent_news = session.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(5).all()
        print("\n=== News Articles ===")
        print(f"Total news articles: {news_count}")
        if recent_news:
            print("Most recent articles:")
            for article in recent_news:
                print(f"- {article.published_at}: {article.headline[:100]}...")
        
        # Check Rankings
        rankings_count = session.query(RankingResult).count()
        recent_rankings = session.query(RankingResult).order_by(RankingResult.analysis_date.desc()).limit(5).all()
        print("\n=== Ranking Results ===")
        print(f"Total ranking records: {rankings_count}")
        if recent_rankings:
            print("Most recent rankings:")
            for rank in recent_rankings:
                print(f"- {rank.security.symbol} on {rank.analysis_date}: Rank #{rank.rank} (Score: {rank.composite_score:.1f})")
        
        # Check Trades
        trades_count = session.query(TradeRecord).count()
        recent_trades = session.query(TradeRecord).order_by(TradeRecord.trade_date.desc()).limit(5).all()
        print("\n=== Trade Records ===")
        print(f"Total trade records: {trades_count}")
        if recent_trades:
            print("Most recent trades:")
            for trade in recent_trades:
                print(f"- {trade.security.symbol}: {trade.trade_type} {trade.quantity} @ ${trade.price}")
                
        # Get table sizes
        table_sizes = session.execute(text("""
            SELECT name, COUNT(*) as count 
            FROM sqlite_master 
            WHERE type='table' 
            GROUP BY name
        """)).fetchall()
        
        print("\n=== Database Tables ===")
        for table, count in table_sizes:
            print(f"Table {table}: {count} rows")
            
    except Exception as e:
        print(f"Error exploring database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    explore_database()
