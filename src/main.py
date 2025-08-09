"""
Main execution script for the Algorithmic Investment Framework

This script demonstrates the core functionality of the framework by running
a complete analysis on a set of predefined stocks and ETFs.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.ranking_engine import create_ranking_engine
from data_acquisition.market_data import create_market_data_manager
from data_acquisition.news_sentiment import create_news_sentiment_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler('logs/framework.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    
    try:
        print("=" * 60)
        print("🚀 ALGORITHMIC INVESTMENT DECISION FRAMEWORK")
        print("=" * 60)
        print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        default_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA',
            'JPM', 'BAC', 'WFC', 'GS',
            'SPY', 'QQQ', 'IWM', 'VTI', 'VOO',
            'KO', 'PEP', 'WMT', 'HD',
            'JNJ', 'PFE', 'UNH'
        ]
        print("🔧 Initializing ranking engine...")
        engine = create_ranking_engine(price_weight=0.6, sentiment_weight=0.4)
        print(f"📊 Analyzing {len(default_tickers)} assets...")
        print("This may take a few minutes as we fetch market data and news...")
        print()
        rankings = engine.rank_assets(default_tickers, include_details=True)
        print("📈 RANKING RESULTS")
        print("-" * 40)
        top_10 = rankings.head(10)
        display_columns = ['rank', 'ticker', 'composite_score', 'technical_score', 'sentiment_score', 'percent_change', 'headline_count']
        pd.set_option('display.precision', 2)
        pd.set_option('display.width', 120)
        print(top_10[display_columns].to_string(index=False))
        print("\n" + "=" * 60)
        print("🎯 TOP INVESTMENT PICKS")
        print("-" * 40)
        top_picks = engine.get_top_picks(default_tickers, top_n=5, min_sentiment_headlines=2)
        for _, pick in top_picks.iterrows():
            print(f"{pick['rank']:2d}. {pick['ticker']:<6} | Score: {pick['composite_score']:5.1f} | "
                  f"{pick['recommendation']:<12} | Change: {pick['percent_change']:+6.2f}% | "
                  f"Headlines: {pick['headline_count']:2d}")
        print("\n" + "=" * 60)
        if len(top_picks) > 0:
            top_ticker = top_picks.iloc[0]['ticker']
            print(f"🔍 DETAILED ANALYSIS: {top_ticker}")
            print("-" * 40)
            detailed_analysis = engine.analyze_single_asset(top_ticker)
            print(f"Company: {detailed_analysis.get('name', 'N/A')}")
            print(f"Sector: {detailed_analysis.get('sector', 'N/A')}")
            print(f"Current Price: ${detailed_analysis.get('price', 0):.2f}")
            print(f"Daily Change: {detailed_analysis.get('percent_change', 0):+.2f}%")
            print(f"Composite Score: {detailed_analysis.get('composite_score', 0):.1f}/100")
            print(f"Technical Score: {detailed_analysis.get('technical_score', 0):.1f}/100")
            print(f"Sentiment Score: {detailed_analysis.get('sentiment_score', 0):.1f}/100")
            print(f"News Headlines: {detailed_analysis.get('headline_count', 0)}")
            print(f"Positive News Ratio: {detailed_analysis.get('positive_ratio', 0):.1%}")
            if 'historical_volatility' in detailed_analysis:
                print(f"3-Month Volatility: {detailed_analysis['historical_volatility']:.2f}%")
            if 'price_trend_3m' in detailed_analysis:
                print(f"3-Month Trend: {detailed_analysis['price_trend_3m']:+.2f}%")
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("-" * 40)
        analysis_meta = rankings.attrs
        print(f"Total Assets Analyzed: {analysis_meta['total_assets']}")
        print(f"Analysis Duration: {analysis_meta['analysis_duration']:.1f} seconds")
        print(f"Price Weight: {analysis_meta['price_weight']:.0%}")
        print(f"Sentiment Weight: {analysis_meta['sentiment_weight']:.0%}")
        print(f"Analysis Timestamp: {analysis_meta['analysis_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nScore Statistics:")
        print(f"  Highest Score: {rankings['composite_score'].max():.1f}")
        print(f"  Lowest Score: {rankings['composite_score'].min():.1f}")
        print(f"  Average Score: {rankings['composite_score'].mean():.1f}")
        print(f"  Median Score: {rankings['composite_score'].median():.1f}")
        # Save results
        output_file = f"data/rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        rankings.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        print("\n" + "=" * 60)
        print("✅ Analysis completed successfully!")
        print("💡 Next steps:")
        print("   1. Review the top picks and their scores")
        print("   2. Launch the dashboard: streamlit run dashboards/main_dashboard.py")
        print("   3. Set up paper trading to test the strategy")
        print("   4. Configure alerts for score changes")
        rankings.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        print("\n" + "=" * 60)
        print("✅ Analysis completed successfully!")
        print("💡 Next steps:")
        print("   1. Review the top picks and their scores")
        print("   2. Launch the dashboard: streamlit run dashboards/main_dashboard.py")
        print("   3. Set up paper trading to test the strategy")
        print("   4. Configure alerts for score changes")
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        print("💡 Check the logs for more details")
        sys.exit(1)


def test_individual_components():
    """Test individual components of the framework"""
    
    print("🧪 TESTING FRAMEWORK COMPONENTS")
    print("=" * 50)
    
    test_tickers = ['AAPL', 'TSLA', 'SPY']
    
    # Test market data
    print("1. Testing market data acquisition...")
    try:
        data_manager = create_market_data_manager()
        price_data = data_manager.get_price_data(test_tickers)
        
        for ticker, data in price_data.items():
            if data['price']:
                print(f"   ✅ {ticker}: ${data['price']:.2f} ({data['percent_change']:+.2f}%)")
            else:
                print(f"   ❌ {ticker}: No data")
                
    except Exception as e:
        print(f"   ❌ Market data test failed: {e}")
    
    # Test sentiment analysis
    print("\n2. Testing sentiment analysis...")
    try:
        sentiment_manager = create_news_sentiment_manager()
        
        for ticker in test_tickers[:2]:  # Test only 2 to save time
            sentiment_data = sentiment_manager.get_sentiment_for_ticker(ticker)
            print(f"   ✅ {ticker}: {sentiment_data['headline_count']} headlines, "
                  f"sentiment: {sentiment_data['average_sentiment']:.3f}")
            
    except Exception as e:
        print(f"   ❌ Sentiment analysis test failed: {e}")
    
    print("\n✅ Component testing completed!")


if __name__ == "__main__":
    # Check if this is a test run
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_individual_components()
    else:
        main()
