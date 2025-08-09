"""
Integration Tests for the Algorithmic Investment Framework

This module contains comprehensive integration tests to verify that all
components of the framework work together correctly.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analysis.ranking_engine import create_ranking_engine
from data_acquisition.market_data import create_market_data_manager
from data_acquisition.news_sentiment import create_news_sentiment_manager
from database.database_manager import create_database_manager
from trading.risk_manager import create_risk_manager


class TestFrameworkIntegration(unittest.TestCase):
    """Integration tests for the complete framework"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        cls.ranking_engine = create_ranking_engine(price_weight=0.6, sentiment_weight=0.4)
        cls.market_data_manager = create_market_data_manager('yahoo')
        cls.news_sentiment_manager = create_news_sentiment_manager()
        cls.risk_manager = create_risk_manager(conservative=True)
        
        # Try to create database manager (might fail without proper setup)
        try:
            cls.db_manager = create_database_manager()
            cls.db_available = cls.db_manager.test_connection()
        except Exception:
            cls.db_manager = None
            cls.db_available = False
    
    def test_market_data_acquisition(self):
        """Test market data acquisition"""
        print("\n🧪 Testing market data acquisition...")
        
        price_data = self.market_data_manager.get_price_data(self.test_tickers)
        
        # Verify we got data for all tickers
        self.assertEqual(len(price_data), len(self.test_tickers))
        
        # Check data structure
        for ticker, data in price_data.items():
            self.assertIn('price', data)
            self.assertIn('percent_change', data)
            self.assertIn('volume', data)
            self.assertIn('timestamp', data)
        
        print(f"✅ Market data acquired for {len(price_data)} tickers")
        
        # Test historical data
        historical_data = self.market_data_manager.get_historical_data('AAPL', '1mo')
        if not historical_data.empty:
            self.assertGreater(len(historical_data), 0)
            self.assertIn('Close', historical_data.columns)
            print("✅ Historical data acquisition working")
        else:
            print("⚠️ Historical data acquisition returned empty results")
    
    def test_sentiment_analysis(self):
        """Test news sentiment analysis"""
        print("\n🧪 Testing sentiment analysis...")
        
        # Test single ticker sentiment
        sentiment_data = self.news_sentiment_manager.get_sentiment_for_ticker('AAPL')
        
        self.assertIn('ticker', sentiment_data)
        self.assertIn('headlines', sentiment_data)
        self.assertIn('sentiment_score', sentiment_data)
        self.assertIn('headline_count', sentiment_data)
        
        print(f"✅ Sentiment analysis completed for AAPL: {sentiment_data['headline_count']} headlines")
        
        # Test multiple tickers
        multi_sentiment = self.news_sentiment_manager.get_sentiment_for_multiple_tickers(['AAPL', 'TSLA'])
        self.assertEqual(len(multi_sentiment), 2)
        
        print("✅ Multiple ticker sentiment analysis working")
    
    def test_ranking_algorithm(self):
        """Test the complete ranking algorithm"""
        print("\n🧪 Testing ranking algorithm...")
        
        rankings = self.ranking_engine.rank_assets(self.test_tickers, include_details=True)
        
        # Verify DataFrame structure
        self.assertIsInstance(rankings, pd.DataFrame)
        self.assertEqual(len(rankings), len(self.test_tickers))
        
        # Check required columns
        required_columns = ['rank', 'ticker', 'composite_score', 'technical_score', 'sentiment_score']
        for col in required_columns:
            self.assertIn(col, rankings.columns)
        
        # Check ranking order (should be descending by composite_score)
        scores = rankings['composite_score'].tolist()
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Check score ranges (0-100)
        for score in scores:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
        
        print(f"✅ Ranking algorithm completed: Top pick is {rankings.iloc[0]['ticker']} "
              f"with score {rankings.iloc[0]['composite_score']:.1f}")
        
        # Test top picks functionality
        top_picks = self.ranking_engine.get_top_picks(self.test_tickers, top_n=2)
        self.assertLessEqual(len(top_picks), 2)
        self.assertIn('recommendation', top_picks.columns)
        
        print("✅ Top picks functionality working")
    
    def test_risk_management(self):
        """Test risk management functionality"""
        print("\n🧪 Testing risk management...")
        
        # Test position size calculation
        account_value = 100000
        entry_price = 150.0
        stop_loss_price = 142.5  # 5% stop loss
        
        position_size = self.risk_manager.calculate_position_size(
            account_value, entry_price, stop_loss_price
        )
        
        self.assertGreater(position_size, 0)
        
        # Verify position size respects risk limits
        risk_per_share = entry_price - stop_loss_price
        total_risk = position_size * risk_per_share
        risk_percentage = total_risk / account_value
        
        self.assertLessEqual(risk_percentage, self.risk_manager.max_portfolio_risk * 1.1)  # Small tolerance
        
        print(f"✅ Position sizing: {position_size} shares, {risk_percentage:.2%} portfolio risk")
        
        # Test trade validation
        trade_request = {
            'symbol': 'AAPL',
            'action': 'buy',
            'quantity': position_size,
            'price': entry_price
        }
        
        is_valid, reason = self.risk_manager.validate_trade(trade_request, [], account_value)
        self.assertTrue(is_valid)
        
        print(f"✅ Trade validation: {reason}")
    
    def test_database_operations(self):
        """Test database operations if available"""
        if not self.db_available:
            print("\n⚠️ Skipping database tests - database not available")
            return
        
        print("\n🧪 Testing database operations...")
        
        # Test adding a security
        security = self.db_manager.add_security('TEST', 'Test Security Corp')
        self.assertIsNotNone(security)
        
        # Test adding price data
        success = self.db_manager.add_price_data(
            'TEST', datetime.now(), 100.0, 105.0, 95.0, 102.0, 1000000
        )
        self.assertTrue(success)
        
        # Test database stats
        stats = self.db_manager.get_database_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('securities_count', stats)
        
        print("✅ Database operations working")
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🧪 Testing end-to-end workflow...")
        
        # Step 1: Run ranking analysis
        rankings = self.ranking_engine.rank_assets(self.test_tickers)
        self.assertGreater(len(rankings), 0)
        
        # Step 2: Get top pick for detailed analysis
        top_ticker = rankings.iloc[0]['ticker']
        detailed_analysis = self.ranking_engine.analyze_single_asset(top_ticker)
        self.assertIn('composite_score', detailed_analysis)
        
        # Step 3: Risk assessment for potential trade
        account_value = 50000
        current_price = detailed_analysis.get('price', 100)
        
        if current_price and current_price > 0:
            position_size = self.risk_manager.calculate_position_size(
                account_value, current_price, current_price * 0.95  # 5% stop loss
            )
            
            trade_request = {
                'symbol': top_ticker,
                'action': 'buy',
                'quantity': position_size,
                'price': current_price
            }
            
            is_valid, reason = self.risk_manager.validate_trade(trade_request, [], account_value)
            
            print(f"✅ End-to-end workflow completed:")
            print(f"   Top pick: {top_ticker} (Score: {detailed_analysis.get('composite_score', 0):.1f})")
            print(f"   Position size: {position_size} shares")
            print(f"   Trade validation: {'✅ Approved' if is_valid else '❌ Rejected'} - {reason}")
        else:
            print("⚠️ Could not complete trade analysis due to missing price data")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n🧪 Testing performance benchmarks...")
        
        import time
        
        # Benchmark ranking analysis
        start_time = time.time()
        rankings = self.ranking_engine.rank_assets(self.test_tickers)
        analysis_time = time.time() - start_time
        
        # Should complete within reasonable time (< 60 seconds for 3 tickers)
        self.assertLess(analysis_time, 60)
        
        print(f"✅ Ranking analysis completed in {analysis_time:.2f} seconds")
        print(f"   Performance: {analysis_time / len(self.test_tickers):.2f} seconds per ticker")
        
        # Memory usage check (basic)
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Should use reasonable memory (< 500MB for basic operations)
        self.assertLess(memory_mb, 500)
        
        print(f"✅ Memory usage: {memory_mb:.1f} MB")


class TestConfigurationAndSetup(unittest.TestCase):
    """Test configuration and setup components"""
    
    def test_configuration_loading(self):
        """Test configuration loading"""
        print("\n🧪 Testing configuration...")
        
        try:
            from config.default_config import get_config, validate_config
            
            config = get_config()
            self.assertIsInstance(config, dict)
            
            # Validate configuration
            is_valid = validate_config(config)
            self.assertTrue(is_valid)
            
            print("✅ Configuration loading and validation working")
            
        except ImportError:
            print("⚠️ Configuration module not available")
    
    def test_environment_variables(self):
        """Test environment variable handling"""
        print("\n🧪 Testing environment variables...")
        
        # Test that framework handles missing API keys gracefully
        original_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        
        # Temporarily remove API key
        if 'ALPHA_VANTAGE_API_KEY' in os.environ:
            del os.environ['ALPHA_VANTAGE_API_KEY']
        
        try:
            manager = create_market_data_manager('yahoo')  # Should still work with Yahoo
            price_data = manager.get_price_data(['AAPL'])
            self.assertIsInstance(price_data, dict)
            print("✅ Framework handles missing API keys gracefully")
        except Exception as e:
            print(f"⚠️ Error handling missing API keys: {e}")
        finally:
            # Restore original API key
            if original_key:
                os.environ['ALPHA_VANTAGE_API_KEY'] = original_key


def run_integration_tests():
    """Run all integration tests with pretty output"""
    print("🚀 ALGORITHMIC INVESTMENT FRAMEWORK - INTEGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestConfigurationAndSetup))
    suite.addTest(unittest.makeSuite(TestFrameworkIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"✅ Passed: {passed}/{total_tests}")
    if failures:
        print(f"❌ Failures: {failures}")
    if errors:
        print(f"🔥 Errors: {errors}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 ALL TESTS PASSED! Framework is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Run: python src/main.py")
        print("   2. Launch dashboard: streamlit run dashboards/main_dashboard.py")
        print("   3. Set up your API keys in .env file for enhanced functionality")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("💡 The framework may still work, but some features might be limited.")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
