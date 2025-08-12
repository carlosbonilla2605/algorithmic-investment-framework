#!/usr/bin/env python3
"""
Quick script to verify that we have methods for all database tables
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.database_manager import DatabaseManager
from database import models
import inspect

def get_table_classes():
    """Get all SQLAlchemy model classes that represent tables"""
    table_classes = []
    for name, obj in inspect.getmembers(models):
        if (inspect.isclass(obj) and 
            hasattr(obj, '__tablename__') and 
            obj.__tablename__ != 'sqlite_master'):
            table_classes.append((name, obj.__tablename__))
    return table_classes

def get_db_methods():
    """Get all methods from DatabaseManager"""
    db_methods = []
    for name, method in inspect.getmembers(DatabaseManager, predicate=inspect.isfunction):
        if not name.startswith('_'):  # Exclude private methods
            db_methods.append(name)
    return db_methods

def main():
    print("🔍 Database Coverage Analysis")
    print("=" * 50)
    
    # Get all table classes
    tables = get_table_classes()
    print(f"\n📊 Found {len(tables)} database tables:")
    for class_name, table_name in tables:
        print(f"  - {class_name} ({table_name})")
    
    # Get all database methods
    methods = get_db_methods()
    print(f"\n🔧 Found {len(methods)} database methods:")
    for method in sorted(methods):
        print(f"  - {method}")
    
    # Check coverage
    print(f"\n✅ Coverage Assessment:")
    
    # Expected method patterns for each table
    coverage = {
        'Security': ['get_or_create_security'],
        'PriceData': ['add_price_data', 'get_latest_prices'],
        'NewsArticle': ['add_news_article'],
        'SecurityNewsLink': ['add_news_article'],  # Implicit via add_news_article
        'ArticleSentiment': ['add_sentiment_analysis'],
        'RankingResult': ['save_ranking_results', 'get_latest_rankings'],
        'TradeRecord': ['record_trade', 'get_trade_history'],
        'Portfolio': ['update_portfolio_snapshot', 'get_portfolio_performance'],
        'Position': ['update_position', 'get_positions', 'get_current_positions'],
        'SystemLog': ['log_system_event', 'get_system_logs', 'get_recent_logs']
    }
    
    all_covered = True
    for table_class, expected_methods in coverage.items():
        print(f"\n  {table_class}:")
        for expected_method in expected_methods:
            if expected_method in methods:
                print(f"    ✅ {expected_method}")
            else:
                print(f"    ❌ {expected_method} - MISSING")
                all_covered = False
    
    print(f"\n{'🎉' if all_covered else '⚠️ '} Summary:")
    if all_covered:
        print("  All tables have appropriate CRUD methods!")
    else:
        print("  Some tables are missing methods - see above")
    
    print(f"\n📈 Statistics:")
    print(f"  Tables: {len(tables)}")
    print(f"  Methods: {len(methods)}")
    print(f"  Coverage: {'Complete' if all_covered else 'Partial'}")

if __name__ == "__main__":
    main()
