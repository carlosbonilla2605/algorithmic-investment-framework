# Algorithmic Investment Decision Framework

A comprehensive Python-based framework for algorithmic stock and ETF analysis, ranking, and trading decisions based on price momentum and news sentiment analysis.

## 🚀 Features

- **Multi-source Data Integration**: Fetch market data from multiple APIs (Alpha Vantage, Polygon.io, Finnhub)
- **Sentiment Analysis**: Analyze financial news sentiment using VADER and FinBERT
- **Intelligent Ranking System**: Composite scoring based on price momentum and news sentiment
- **Interactive Dashboard**: Real-time Streamlit dashboard for visualization and analysis
- **Automated Trading**: Integration with Alpaca API for paper and live trading
- **Risk Management**: Built-in position sizing and stop-loss mechanisms
- **Machine Learning Ready**: Framework for advanced ML-based ranking models
- **Database Storage**: Support for PostgreSQL/TimescaleDB and InfluxDB

## 📁 Project Structure

```
algorithmic-investment-framework/
├── src/
│   ├── data_acquisition/     # API integrations and data fetching
│   ├── analysis/            # Ranking algorithms and sentiment analysis
│   ├── dashboard/           # Streamlit dashboard components
│   ├── trading/             # Trading execution and risk management
│   ├── database/            # Database models and operations
│   └── utils/               # Utility functions and helpers
├── config/                  # Configuration files
├── data/                    # Local data storage
├── logs/                    # Application logs
├── tests/                   # Unit and integration tests
├── dashboards/              # Dashboard deployment files
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🛠 Quick Start

### 1. Clone and Setup

```bash
cd algorithmic-investment-framework
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp env_example.txt .env
# Edit .env with your actual API keys
```

### 3. Download NLTK Data

```python
import nltk
nltk.download('vader_lexicon')
```

### 4. Run the Core Ranking System

```bash
python src/main.py
```

### 5. Launch the Dashboard

```bash
streamlit run dashboards/main_dashboard.py
```

## 🔑 API Keys Required

- **Alpha Vantage**: Free tier available at [alphavantage.co](https://www.alphavantage.co/)
- **Polygon.io**: Free tier available at [polygon.io](https://polygon.io/)
- **Finnhub**: Free tier available at [finnhub.io](https://finnhub.io/)
- **Alpaca**: Paper trading free at [alpaca.markets](https://alpaca.markets/)

## 📊 Usage Examples

### Basic Stock Ranking
```python
from src.analysis.ranking_engine import RankingEngine

engine = RankingEngine()
rankings = engine.rank_assets(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])
print(rankings)
```

### Dashboard Access
Once running, access the dashboard at `http://localhost:8501`

## ⚠️ Risk Disclaimer

This framework is for educational and research purposes. Always:
- Start with paper trading
- Implement proper risk management
- Understand the legal and regulatory requirements
- Never risk more than you can afford to lose

## 🏗 Architecture

The framework follows a modular architecture:
- **Data Layer**: Handles all external API interactions
- **Analysis Layer**: Processes data and generates rankings
- **Visualization Layer**: Provides interactive dashboards
- **Trading Layer**: Executes trades and manages risk
- **Storage Layer**: Persists data for analysis and backtesting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support, please open an issue in the GitHub repository.
