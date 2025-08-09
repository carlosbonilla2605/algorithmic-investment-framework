#!/usr/bin/env python3
"""
Quick Start Script for the Algorithmic Investment Framework

This script provides a simple way to get started with the framework
and checks that everything is working correctly.
"""

import sys
import os
import subprocess

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. You have {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} - Good!")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def download_nltk_data():
    """Download required NLTK data"""
    print("\n📚 Downloading NLTK data...")
    
    try:
        import nltk
        nltk.download('vader_lexicon', quiet=True)
        print("✅ NLTK data downloaded!")
        return True
    except Exception as e:
        print(f"❌ Failed to download NLTK data: {e}")
        return False


def check_environment():
    """Check environment setup"""
    print("\n🔧 Checking environment setup...")
    
    env_file = ".env"
    env_example = "env_example.txt"
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print(f"⚠️ No .env file found. Please copy {env_example} to .env and add your API keys.")
            print(f"   You can run: cp {env_example} .env")
        else:
            print("⚠️ No environment files found. The framework will use default settings.")
        return False
    
    print("✅ Environment file found!")
    
    # Check for API keys
    with open(env_file, 'r') as f:
        content = f.read()
    
    api_keys = ['ALPHA_VANTAGE_API_KEY', 'ALPACA_API_KEY']
    found_keys = []
    
    for key in api_keys:
        if key in content and 'your_' not in content:
            found_keys.append(key)
    
    if found_keys:
        print(f"✅ Found API keys: {', '.join(found_keys)}")
    else:
        print("⚠️ No API keys configured. The framework will work with limited functionality.")
    
    return True


def run_basic_test():
    """Run a basic functionality test"""
    print("\n🧪 Running basic functionality test...")
    
    # Add src to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        # Test market data
        from data_acquisition.market_data import create_market_data_manager
        
        manager = create_market_data_manager('yahoo')
        test_data = manager.get_price_data(['AAPL'])
        
        if test_data and 'AAPL' in test_data:
            print("✅ Market data acquisition working!")
        else:
            print("⚠️ Market data test returned empty results")
            
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False
    
    try:
        # Test sentiment analysis
        from data_acquisition.news_sentiment import create_news_sentiment_manager
        
        sentiment_manager = create_news_sentiment_manager()
        sentiment_data = sentiment_manager.get_sentiment_for_ticker('AAPL')
        
        if sentiment_data and 'sentiment_score' in sentiment_data:
            print("✅ Sentiment analysis working!")
        else:
            print("⚠️ Sentiment analysis test completed with warnings")
            
    except Exception as e:
        print(f"❌ Sentiment analysis test failed: {e}")
        return False
    
    try:
        # Test ranking engine
        from analysis.ranking_engine import create_ranking_engine
        
        engine = create_ranking_engine()
        rankings = engine.rank_assets(['AAPL', 'MSFT'])
        
        if not rankings.empty:
            print("✅ Ranking engine working!")
            print(f"   Sample result: {rankings.iloc[0]['ticker']} scored {rankings.iloc[0]['composite_score']:.1f}")
        else:
            print("⚠️ Ranking engine test returned empty results")
            
    except Exception as e:
        print(f"❌ Ranking engine test failed: {e}")
        return False
    
    return True


def show_next_steps():
    """Show next steps to the user"""
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 50)
    print("\n🚀 Quick Start Options:")
    print("\n1. Run a simple analysis:")
    print("   python src/main.py")
    
    print("\n2. Launch the interactive dashboard:")
    print("   streamlit run dashboards/main_dashboard.py")
    
    print("\n3. Try the examples:")
    print("   python run_example.py")
    
    print("\n4. Run integration tests:")
    print("   python tests/test_integration.py")
    
    print("\n💡 Tips:")
    print("   • Start with the dashboard for the best experience")
    print("   • Add your API keys to .env for enhanced functionality") 
    print("   • Check SETUP_GUIDE.md for detailed instructions")
    print("   • Begin with paper trading if you want to test trading features")
    
    print("\n📚 Documentation:")
    print("   • README.md - Project overview")
    print("   • SETUP_GUIDE.md - Detailed setup instructions")
    print("   • src/ - Source code with inline documentation")
    
    print("\n⚖️ Remember: This is for educational purposes. Always understand")
    print("   the risks before making any investment decisions!")


def main():
    """Main setup function"""
    print("🚀 ALGORITHMIC INVESTMENT FRAMEWORK - QUICK START")
    print("=" * 60)
    print("This script will help you set up the framework quickly.\n")
    
    # Step 1: Check Python version
    if not check_python_version():
        print("\n❌ Setup failed. Please upgrade Python and try again.")
        sys.exit(1)
    
    # Step 2: Install dependencies
    print("\nDo you want to install dependencies? (y/n): ", end="")
    if input().lower().startswith('y'):
        if not install_dependencies():
            print("\n❌ Setup failed. Please check the error above.")
            sys.exit(1)
    
    # Step 3: Download NLTK data
    if not download_nltk_data():
        print("\n⚠️ NLTK data download failed, but continuing...")
    
    # Step 4: Check environment
    check_environment()
    
    # Step 5: Run basic test
    print("\nDo you want to run a basic functionality test? (y/n): ", end="")
    if input().lower().startswith('y'):
        if run_basic_test():
            print("\n✅ All basic tests passed!")
        else:
            print("\n⚠️ Some tests failed, but the framework should still work.")
    
    # Step 6: Show next steps
    show_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)
