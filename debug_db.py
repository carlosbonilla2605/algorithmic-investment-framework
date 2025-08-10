"""
Debug script to test database operations step by step
"""
from src.database.database_manager import DatabaseManager
from src.database.models import Security, NewsArticle, ArticleSentiment, SecurityNewsLink
from datetime import datetime

def test_db_operations():
    db = DatabaseManager()
    print("1. Created DatabaseManager instance")
    
    with db.get_session() as session:
        print("2. Got database session")
        
        # Test 1: Create and retrieve a security
        print("\nTest 1: Security Creation")
        security = db.get_or_create_security("AAPL", session=session)
        print(f"Security created/retrieved: {security.id=}, {security.symbol=}")
        
        # Test 2: Create a news article
        print("\nTest 2: News Article Creation")
        news = NewsArticle(
            headline="Test headline",
            published_at=datetime.now(),
            source="test"
        )
        session.add(news)
        session.flush()  # This gets us the ID without committing
        print(f"News article created: {news.id=}")
        
        # Test 3: Create security-news link
        print("\nTest 3: Security-News Link Creation")
        link = SecurityNewsLink(
            security_id=security.id,
            article_id=news.id,
            relevance_score=1.0
        )
        session.add(link)
        
        # Test 4: Create sentiment
        print("\nTest 4: Sentiment Creation")
        sent = ArticleSentiment(
            article_id=news.id,
            sentiment_model='vader',
            compound_score=0.5,
            positive_score=0.6,
            negative_score=0.1,
            neutral_score=0.3
        )
        session.add(sent)
        
        print("\nAttempting to commit all changes...")
        session.commit()
        print("Changes committed successfully!")
        
        # Test 5: Verify data was saved
        print("\nTest 5: Data Verification")
        saved_security = session.query(Security).filter_by(symbol="AAPL").first()
        saved_news = session.query(NewsArticle).filter_by(id=news.id).first()
        saved_sentiment = session.query(ArticleSentiment).filter_by(article_id=news.id).first()
        
        print(f"Retrieved security: {saved_security.symbol}")
        print(f"Retrieved news: {saved_news.headline}")
        print(f"Retrieved sentiment: {saved_sentiment.compound_score}")

if __name__ == "__main__":
    test_db_operations()
