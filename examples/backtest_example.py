#!/usr/bin/env python3
"""
Backtesting Example Script

This script demonstrates how to use the new backtesting functionality
to test investment strategies on historical data.

TASK-031: Add a lightweight backtest runner over historical daily data
TASK-032: Report CAGR, Sharpe, and max drawdown

Usage:
    python examples/backtest_example.py
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.analysis.backtesting import create_backtesting_engine, BacktestResult
from src.analysis.ranking_engine import create_ranking_engine
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_example_backtest():
    """
    Run an example backtest to demonstrate the functionality
    """
    
    print("=" * 60)
    print("🔬 BACKTESTING EXAMPLE")
    print("=" * 60)
    print()
    
    # Configuration
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    start_date = '2023-01-01'
    end_date = '2023-06-30'  # Shorter period for demo
    initial_capital = 100000
    
    print(f"📊 Configuration:")
    print(f"   Tickers: {', '.join(tickers)}")
    print(f"   Period: {start_date} to {end_date}")
    print(f"   Initial Capital: ${initial_capital:,}")
    print(f"   Strategy: Top 3 momentum picks, rebalanced monthly")
    print()
    
    try:
        # Create the backtesting engine
        print("🔧 Initializing engines...")
        ranking_engine = create_ranking_engine(
            price_weight=0.8,  # Emphasize price momentum for this example
            sentiment_weight=0.2
        )
        
        backtest_engine = create_backtesting_engine(
            ranking_engine=ranking_engine,
            initial_capital=initial_capital,
            rebalance_frequency='monthly',
            top_n_picks=3,
            transaction_cost=0.001,  # 0.1% transaction cost
            max_position_size=0.40   # Max 40% per position
        )
        
        # Run the backtest
        print("🚀 Running backtest simulation...")
        print("   (This may take a moment due to data fetching...)")
        print()
        
        result = backtest_engine.run_backtest(tickers, start_date, end_date)
        
        # Display results
        print("✅ Backtest completed!")
        print()
        print("📈 PERFORMANCE SUMMARY")
        print("-" * 40)
        
        summary = result.summary()
        for key, value in summary.items():
            print(f"   {key:20}: {value}")
        
        print()
        print("💡 INSIGHTS")
        print("-" * 40)
        
        # Provide some basic insights
        if result.cagr > 0.10:
            print("   ✅ Strong annual returns (>10%)")
        elif result.cagr > 0.05:
            print("   ⚠️  Moderate annual returns (5-10%)")
        else:
            print("   ❌ Low annual returns (<5%)")
            
        if result.sharpe_ratio > 1.0:
            print("   ✅ Excellent risk-adjusted returns (Sharpe > 1.0)")
        elif result.sharpe_ratio > 0.5:
            print("   ⚠️  Good risk-adjusted returns (Sharpe 0.5-1.0)")
        else:
            print("   ❌ Poor risk-adjusted returns (Sharpe < 0.5)")
            
        if result.max_drawdown < 0.10:
            print("   ✅ Low maximum drawdown (<10%)")
        elif result.max_drawdown < 0.20:
            print("   ⚠️  Moderate maximum drawdown (10-20%)")
        else:
            print("   ❌ High maximum drawdown (>20%)")
        
        print()
        print("📊 PORTFOLIO PROGRESSION")
        print("-" * 40)
        
        if result.portfolio_values and len(result.portfolio_values) >= 2:
            print(f"   Start Value: ${result.portfolio_values[0]:,.2f}")
            print(f"   End Value:   ${result.portfolio_values[-1]:,.2f}")
            print(f"   Total P&L:   ${result.portfolio_values[-1] - result.portfolio_values[0]:,.2f}")
        
        if result.trade_history:
            print(f"   Total Trades: {len(result.trade_history)}")
            
            # Show some recent trades
            print()
            print("📋 RECENT TRADES")
            print("-" * 40)
            recent_trades = result.trade_history[-5:] if len(result.trade_history) > 5 else result.trade_history
            
            for trade in recent_trades:
                date_str = trade['date'].strftime('%Y-%m-%d') if hasattr(trade['date'], 'strftime') else str(trade['date'])
                print(f"   {date_str}: {trade['type']} {trade['shares']:.1f} {trade['ticker']} @ ${trade['price']:.2f}")
        
        print()
        print("⚠️  IMPORTANT NOTES")
        print("-" * 40)
        print("   • This is a demonstration with limited historical data")
        print("   • Past performance does not guarantee future results")
        print("   • Always start with paper trading before using real money")
        print("   • Consider transaction costs and market conditions")
        
        return result
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        print("   This might be due to:")
        print("   • Network connectivity issues")
        print("   • Insufficient historical data")
        print("   • API rate limits")
        print()
        print("   Try running again or use the dashboard for interactive backtesting.")
        return None


def demonstrate_different_strategies():
    """
    Demonstrate how different strategy parameters affect results
    """
    
    print()
    print("=" * 60)
    print("🔄 STRATEGY COMPARISON DEMO")
    print("=" * 60)
    print()
    
    strategies = [
        {
            'name': 'Momentum Focus',
            'price_weight': 0.9,
            'sentiment_weight': 0.1,
            'description': 'Emphasizes price momentum over sentiment'
        },
        {
            'name': 'Balanced Approach',
            'price_weight': 0.6,
            'sentiment_weight': 0.4,
            'description': 'Balanced price and sentiment analysis'
        },
        {
            'name': 'Sentiment Focus',
            'price_weight': 0.3,
            'sentiment_weight': 0.7,
            'description': 'Emphasizes news sentiment over price'
        }
    ]
    
    print("📊 Comparing different strategy approaches:")
    print()
    
    for strategy in strategies:
        print(f"Strategy: {strategy['name']}")
        print(f"   Price Weight: {strategy['price_weight']:.1%}")
        print(f"   Sentiment Weight: {strategy['sentiment_weight']:.1%}")
        print(f"   Description: {strategy['description']}")
        print()
    
    print("💡 Run individual backtests for each strategy to compare performance!")
    print("   Use the dashboard for interactive comparison and visualization.")


if __name__ == "__main__":
    print("🚀 Starting Backtesting Example...")
    print()
    
    # Run the main example
    result = run_example_backtest()
    
    # Show strategy comparison info
    demonstrate_different_strategies()
    
    print()
    print("🎯 Next Steps:")
    print("   1. Launch the dashboard: python -m streamlit run dashboards/main_dashboard.py")
    print("   2. Go to the '🔬 Backtesting' tab")
    print("   3. Configure your own backtest parameters")
    print("   4. Compare different strategies and time periods")
    print()
    print("Happy backtesting! 📈")