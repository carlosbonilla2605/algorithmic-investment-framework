# 🚀 Algorithmic Investment Framework - Complete Setup Guide

This guide will walk you through setting up the Algorithmic Investment Decision Framework from scratch.

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** (Python 3.9+ recommended)
- **4GB+ RAM** (8GB+ recommended for better performance)
- **Internet connection** for API calls and data fetching
- **Operating System**: Windows 10+, macOS 10.14+, or Linux

### Required API Keys
Before starting, you'll need to sign up for these free services:

1. **Alpha Vantage** (Optional but recommended)
   - Sign up: https://www.alphavantage.co/support/#api-key
   - Free tier: 5 API calls per minute, 500 calls per day

2. **Polygon.io** (Optional for enhanced data)
   - Sign up: https://polygon.io/
   - Free tier: 5 API calls per minute

3. **Finnhub** (Optional for news data)
   - Sign up: https://finnhub.io/register
   - Free tier: 60 API calls per minute

4. **Alpaca Trading** (For paper/live trading)
   - Sign up: https://alpaca.markets/
   - Start with paper trading (free)

## 🛠 Installation Steps

### Step 1: Clone or Download the Project

```bash
# If you have git installed
git clone <repository-url>
cd algorithmic-investment-framework

# Or download and extract the ZIP file to your desired location
```

### Step 2: Create a Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Download NLTK data for sentiment analysis
python -c "import nltk; nltk.download('vader_lexicon')"
```

### Step 4: Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp env_example.txt .env
   ```

2. **Edit the `.env` file** with your actual API keys:
   ```bash
   # Use any text editor
   nano .env
   # or
   code .env  # if using VS Code
   ```

3. **Required Environment Variables:**
   ```env
   # Alpha Vantage (recommended)
   ALPHA_VANTAGE_API_KEY=your_actual_key_here
   
   # Alpaca (for trading - start with paper trading)
   ALPACA_API_KEY=your_alpaca_paper_key
   ALPACA_SECRET_KEY=your_alpaca_paper_secret
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   
   # Optional: Database (SQLite will be used by default)
   # DB_HOST=localhost
   # DB_PORT=5432
   # DB_NAME=investment_framework
   # DB_USER=your_username
   # DB_PASSWORD=your_password
   ```

### Step 5: Test the Installation

```bash
# Test core components
cd src
python main.py test

# If successful, you should see:
# ✅ Market data test passed
# ✅ Sentiment analysis test passed
# ✅ Component testing completed!
```

## 🚦 Quick Start - Your First Analysis

### Option 1: Command Line Analysis

```bash
# Run a complete analysis
cd src
python main.py

# This will:
# 1. Fetch market data for default stocks/ETFs
# 2. Analyze news sentiment
# 3. Generate rankings
# 4. Display top picks
# 5. Save results to CSV
```

### Option 2: Interactive Dashboard

```bash
# Launch the Streamlit dashboard
cd dashboards
streamlit run main_dashboard.py

# Your browser will open to http://localhost:8501
# You can now interactively analyze any stocks/ETFs!
```

## 📊 Understanding the Results

### Composite Score (0-100)
- **80-100**: Strong Buy (High confidence)
- **65-79**: Buy (Good opportunity)
- **50-64**: Hold (Neutral)
- **35-49**: Weak Hold (Consider selling)
- **0-34**: Avoid (High risk)

### Score Components
- **Technical Score**: Based on price momentum and volume
- **Sentiment Score**: Based on recent news analysis
- **Final Score**: Weighted combination (default: 60% technical, 40% sentiment)

## 🔧 Advanced Configuration

### Customizing Algorithm Weights

Edit in your scripts or dashboard:
```python
# More emphasis on price momentum
engine = create_ranking_engine(price_weight=0.8, sentiment_weight=0.2)

# More emphasis on news sentiment
engine = create_ranking_engine(price_weight=0.4, sentiment_weight=0.6)
```

### Adding Your Own Stock Lists

In the dashboard or modify `src/main.py`:
```python
# Your custom watchlist
my_stocks = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'COIN']
rankings = engine.rank_assets(my_stocks)
```

### Database Setup (Optional)

For production use, set up PostgreSQL:

1. **Install PostgreSQL**
2. **Create database:**
   ```sql
   CREATE DATABASE investment_framework;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE investment_framework TO your_username;
   ```
3. **Update `.env` file** with PostgreSQL credentials
4. **The framework will automatically create all tables**

## 📈 Trading Integration (Paper Trading)

### Set up Alpaca Paper Trading

1. **Sign up** at https://alpaca.markets/
2. **Get your paper trading keys** from the dashboard
3. **Update `.env`** with your Alpaca credentials:
   ```env
   ALPACA_API_KEY=your_paper_key
   ALPACA_SECRET_KEY=your_paper_secret
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

### Test Trading Integration

```python
from src.trading.alpaca_client import create_alpaca_client

# Create client (paper trading by default)
client = create_alpaca_client(paper_trading=True)

# Check account
account_info = client.get_account_info()
print(f"Paper Trading Account: ${account_info['portfolio_value']:,.2f}")

# Execute trades based on rankings (paper money!)
rankings = engine.rank_assets(['AAPL', 'MSFT', 'GOOGL'])
trade_results = client.execute_ranking_based_trade(rankings, top_n=3, investment_amount=1000)
```

## 🚨 Important Safety Notes

### For Beginners
1. **Always start with paper trading**
2. **Never risk more than you can afford to lose**
3. **Understand that past performance doesn't guarantee future results**
4. **This is an educational tool - not financial advice**

### Risk Management
- Default settings limit each position to 2% of portfolio risk
- Built-in stop-loss and take-profit mechanisms
- Daily trading limits to prevent overtrading
- Position size limits to ensure diversification

## 🔍 Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**2. "API key not found" warnings**
- Check your `.env` file exists and has the correct keys
- Ensure no extra spaces around the `=` sign
- The framework will still work with Yahoo Finance data if API keys are missing

**3. "No data available" for certain stocks**
- Some stocks might not have recent news (sentiment score will be neutral)
- Very new or delisted stocks might not have complete data
- Try with well-known stocks first (AAPL, MSFT, GOOGL)

**4. Dashboard not loading**
```bash
# Install streamlit if missing
pip install streamlit

# Check if port 8501 is available
# Try different port if needed
streamlit run main_dashboard.py --server.port 8502
```

**5. Slow performance**
- Increase delays between API calls in the code
- Use fewer stocks in your analysis initially
- Consider upgrading to paid API tiers for faster access

### Getting Help

1. **Check the logs** in the `logs/` directory
2. **Review error messages** carefully
3. **Start with the test mode**: `python main.py test`
4. **Use smaller stock lists** for testing

## 📚 Next Steps

### Once Everything is Working

1. **Experiment with different stock lists**
2. **Try different algorithm weights**
3. **Set up automated daily analysis**
4. **Explore the database features**
5. **Consider integrating additional data sources**

### Advanced Features to Explore

1. **Backtesting**: Test your strategy on historical data
2. **Custom Indicators**: Add your own technical indicators
3. **Machine Learning**: Implement ML-based ranking models
4. **Alerts**: Set up notifications for high-scoring opportunities
5. **Portfolio Optimization**: Advanced position sizing and rebalancing

### Deployment Options

1. **Cloud Deployment**: Run on AWS, Google Cloud, or Azure
2. **Scheduled Execution**: Set up daily automated analysis
3. **Web Hosting**: Deploy the dashboard for remote access
4. **Mobile Alerts**: Integrate with notification services

## ⚖️ Legal Disclaimer

This software is for educational purposes only. It is not financial advice and should not be relied upon for making investment decisions. Always consult with a qualified financial advisor before making investment decisions. The developers are not responsible for any financial losses incurred through the use of this software.

## 🤝 Contributing

Interested in improving the framework? Here's how you can help:

1. **Report bugs** or suggest features
2. **Improve documentation** 
3. **Add new data sources** or indicators
4. **Enhance the dashboard** with new visualizations
5. **Implement backtesting** features

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Investing! 📈**

Remember: Start small, learn continuously, and never risk more than you can afford to lose.
