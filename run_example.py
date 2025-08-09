#!/usr/bin/env python3
"""
Example Runner for the Algorithmic Investment Framework

This script demonstrates how to use the framework with different configurations
and provides examples of all major functionality.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def example_basic_analysis():
    """Basic ranking analysis example"""
    print("\n🔵 EXAMPLE 1: Basic Ranking Analysis")
    print("-" * 50)
    
    from analysis.ranking_engine import create_ranking_engine
    
    # Create ranking engine with default settings
    engine = create_ranking_engine(price_weight=0.6, sentiment_weight=0.4)
    
    # Analyze a small set of popular stocks
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"Analyzing {len(tickers)} stocks: {', '.join(tickers)}")
    
    try:
        # Run the analysis
        rankings = engine.rank_assets(tickers, include_details=False)
        
        print("\n📊 Results:")
        print(rankings[['rank', 'ticker', 'composite_score', 'technical_score', 'sentiment_score']].to_string(index=False))
        
        # Get top pick details
        top_pick = rankings.iloc[0]
        print(f"\n🎯 Top Pick: {top_pick['ticker']} with score {top_pick['composite_score']:.1f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_custom_weights():
    """Example with custom algorithm weights"""
    print("\n🔵 EXAMPLE 2: Custom Algorithm Weights")
    print("-" * 50)
    
    from analysis.ranking_engine import create_ranking_engine
    
    tickers = ['NVDA', 'AMD', 'INTC', 'TSM']
    
    # Compare different weight configurations
    configs = [
        {"price_weight": 0.8, "sentiment_weight": 0.2, "name": "Price-Focused"},
        {"price_weight": 0.4, "sentiment_weight": 0.6, "name": "Sentiment-Focused"},
        {"price_weight": 0.5, "sentiment_weight": 0.5, "name": "Balanced"}
    ]
    
    for config in configs:
        print(f"\n{config['name']} Strategy ({config['price_weight']:.0%} price, {config['sentiment_weight']:.0%} sentiment):")
        
        try:
            engine = create_ranking_engine(config['price_weight'], config['sentiment_weight'])
            rankings = engine.rank_assets(tickers)
            
            for _, row in rankings.head(2).iterrows():
                print(f"  {row['rank']}. {row['ticker']}: {row['composite_score']:.1f}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


def example_etf_analysis():
    """Example analyzing ETFs"""
    print("\n🔵 EXAMPLE 3: ETF Analysis")
    print("-" * 50)
    
    from analysis.ranking_engine import create_ranking_engine
    
    # Popular ETFs across different sectors
    etfs = ['SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'XLK', 'XLV']
    
    print(f"Analyzing {len(etfs)} ETFs: {', '.join(etfs)}")
    
    try:
        engine = create_ranking_engine()
        rankings = engine.rank_assets(etfs, include_details=True)
        
        print("\n📊 ETF Rankings:")
        for _, row in rankings.iterrows():
            print(f"{row['rank']:2d}. {row['ticker']:<4} | Score: {row['composite_score']:5.1f} | "
                  f"Change: {row['percent_change']:+6.2f}% | Headlines: {row['headline_count']:2d}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_detailed_analysis():
    """Example of detailed single-asset analysis"""
    print("\n🔵 EXAMPLE 4: Detailed Single Asset Analysis")
    print("-" * 50)
    
    from analysis.ranking_engine import create_ranking_engine
    
    symbol = 'AAPL'
    print(f"Detailed analysis for {symbol}:")
    
    try:
        engine = create_ranking_engine()
        detailed_data = engine.analyze_single_asset(symbol)
        
        print(f"\n📈 {symbol} Analysis:")
        print(f"  Company: {detailed_data.get('name', 'N/A')}")
        print(f"  Sector: {detailed_data.get('sector', 'N/A')}")
        print(f"  Current Price: ${detailed_data.get('price', 0):.2f}")
        print(f"  Daily Change: {detailed_data.get('percent_change', 0):+.2f}%")
        print(f"  Composite Score: {detailed_data.get('composite_score', 0):.1f}/100")
        print(f"  Technical Score: {detailed_data.get('technical_score', 0):.1f}/100")
        print(f"  Sentiment Score: {detailed_data.get('sentiment_score', 0):.1f}/100")
        print(f"  News Headlines: {detailed_data.get('headline_count', 0)}")
        print(f"  Positive News: {detailed_data.get('positive_ratio', 0):.1%}")
        
        if 'historical_volatility' in detailed_data:
            print(f"  Volatility (3m): {detailed_data['historical_volatility']:.2f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_risk_management():
    """Example of risk management features"""
    print("\n🔵 EXAMPLE 5: Risk Management")
    print("-" * 50)
    
    from trading.risk_manager import create_risk_manager
    
    # Create conservative risk manager
    risk_manager = create_risk_manager(conservative=True)
    
    # Example portfolio
    account_value = 100000
    positions = [
        {'symbol': 'AAPL', 'market_value': 8000},
        {'symbol': 'MSFT', 'market_value': 6000},
        {'symbol': 'GOOGL', 'market_value': 5000},
    ]
    
    print(f"Portfolio Value: ${account_value:,}")
    print(f"Current Positions: {len(positions)}")
    
    # Get risk summary
    try:
        risk_summary = risk_manager.get_risk_summary(account_value, positions)
        
        print(f"\n🛡️ Risk Summary:")
        print(f"  Total Exposure: {risk_summary['portfolio_risk']['total_exposure']:.1%}")
        print(f"  Largest Position: {risk_summary['portfolio_risk']['largest_position_pct']:.1%}")
        print(f"  Diversification Score: {risk_summary['portfolio_risk']['diversification_score']:.0f}/100")
        print(f"  Concentration Risk: {risk_summary['portfolio_risk']['concentration_risk']}")
        
        # Test position sizing
        entry_price = 150.0
        stop_loss_price = 142.5  # 5% stop loss
        
        position_size = risk_manager.calculate_position_size(
            account_value, entry_price, stop_loss_price
        )
        
        print(f"\n📏 Position Sizing Example:")
        print(f"  Entry Price: ${entry_price:.2f}")
        print(f"  Stop Loss: ${stop_loss_price:.2f}")
        print(f"  Recommended Size: {position_size} shares")
        print(f"  Total Investment: ${position_size * entry_price:,.2f}")
        
        # Test trade validation
        trade_request = {
            'symbol': 'NVDA',
            'action': 'buy',
            'quantity': position_size,
            'price': entry_price
        }
        
        is_valid, reason = risk_manager.validate_trade(trade_request, positions, account_value)
        print(f"  Trade Validation: {'✅ Approved' if is_valid else '❌ Rejected'} - {reason}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_paper_trading():
    """Example of paper trading integration"""
    print("\n🔵 EXAMPLE 6: Paper Trading Integration")
    print("-" * 50)
    
    try:
        from trading.alpaca_client import create_alpaca_client
        
        # Create paper trading client
        client = create_alpaca_client(paper_trading=True)
        
        if client:
            # Get account info
            account_info = client.get_account_info()
            
            print("📊 Paper Trading Account:")
            print(f"  Status: {account_info.get('status', 'Unknown')}")
            print(f"  Buying Power: ${account_info.get('buying_power', 0):,.2f}")
            print(f"  Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
            print(f"  Cash: ${account_info.get('cash', 0):,.2f}")
            
            # Get current positions
            positions = client.get_positions()
            if positions:
                print(f"\n📋 Current Positions ({len(positions)}):")
                for pos in positions[:5]:  # Show first 5
                    print(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']:.2f} "
                          f"(P&L: ${pos['unrealized_pl']:+.2f})")
            else:
                print("\n📋 No current positions")
            
            # Get recent orders
            orders = client.get_orders(limit=5)
            if orders:
                print(f"\n📋 Recent Orders ({len(orders)}):")
                for order in orders:
                    print(f"  {order['symbol']}: {order['side']} {order['qty']} @ {order['status']}")
            
        else:
            print("⚠️ Could not connect to Alpaca (API keys may be missing)")
            print("💡 Set up your Alpaca paper trading keys in .env file to enable trading features")
            
    except ImportError:
        print("⚠️ Alpaca library not installed")
        print("💡 Install with: pip install alpaca-py")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_database_operations():
    """Example of database operations"""
    print("\n🔵 EXAMPLE 7: Database Operations")
    print("-" * 50)
    
    try:
        from database.database_manager import create_database_manager
        
        # Create database manager
        db_manager = create_database_manager()
        
        if db_manager.test_connection():
            print("✅ Database connection successful")
            
            # Get database stats
            stats = db_manager.get_database_stats()
            
            print("\n📊 Database Statistics:")
            print(f"  Securities: {stats.get('securities_count', 0)}")
            print(f"  Price Records: {stats.get('price_records_count', 0)}")
            print(f"  News Articles: {stats.get('news_articles_count', 0)}")
            print(f"  Rankings: {stats.get('ranking_results_count', 0)}")
            print(f"  Trades: {stats.get('trade_records_count', 0)}")
            
            # Show latest data dates
            if stats.get('latest_price_date'):
                print(f"  Latest Price Data: {stats['latest_price_date'].strftime('%Y-%m-%d')}")
            if stats.get('latest_news_date'):
                print(f"  Latest News: {stats['latest_news_date'].strftime('%Y-%m-%d')}")
            
            print("\n💡 Database is available for storing analysis results and trade history")
            
        else:
            print("⚠️ Database connection failed")
            print("💡 Framework will work without database, but historical data won't be stored")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_performance_comparison():
    """Example comparing different strategies"""
    print("\n🔵 EXAMPLE 8: Strategy Performance Comparison")
    print("-" * 50)
    
    from analysis.ranking_engine import create_ranking_engine
    
    # Test tickers
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
    
    strategies = [
        {"name": "Momentum Focus", "price": 0.8, "sentiment": 0.2},
        {"name": "News Focus", "price": 0.3, "sentiment": 0.7},
        {"name": "Balanced", "price": 0.5, "sentiment": 0.5},
    ]
    
    print("🏁 Strategy Comparison:")
    
    try:
        results = {}
        
        for strategy in strategies:
            engine = create_ranking_engine(strategy["price"], strategy["sentiment"])
            rankings = engine.rank_assets(tickers)
            
            # Get top 3 picks
            top_3 = rankings.head(3)['ticker'].tolist()
            avg_score = rankings.head(3)['composite_score'].mean()
            
            results[strategy["name"]] = {
                'top_3': top_3,
                'avg_score': avg_score
            }
        
        # Display results
        for strategy_name, result in results.items():
            print(f"\n{strategy_name}:")
            print(f"  Top 3: {', '.join(result['top_3'])}")
            print(f"  Avg Score: {result['avg_score']:.1f}")
        
        print("\n💡 Different strategies may identify different opportunities!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("🚀 ALGORITHMIC INVESTMENT FRAMEWORK - EXAMPLES")
    print("=" * 60)
    print("This script demonstrates key features of the framework.")
    print("Note: Examples may take a few minutes to complete due to API calls.\n")
    
    examples = [
        example_basic_analysis,
        example_custom_weights,
        example_etf_analysis,
        example_detailed_analysis,
        example_risk_management,
        example_paper_trading,
        example_database_operations,
        example_performance_comparison
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except KeyboardInterrupt:
            print(f"\n❌ Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
        
        if i < len(examples):
            input(f"\nPress Enter to continue to Example {i+1}...")
    
    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("\n💡 Next steps:")
    print("   1. Run the main analysis: python src/main.py")
    print("   2. Launch the dashboard: streamlit run dashboards/main_dashboard.py")
    print("   3. Run integration tests: python tests/test_integration.py")
    print("   4. Set up your API keys in .env for enhanced functionality")


if __name__ == "__main__":
    main()
