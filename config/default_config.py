"""
Default Configuration Settings for the Algorithmic Investment Framework

This module contains default configuration settings that can be overridden
by environment variables or user preferences.
"""

import os
from typing import Dict, List, Any

# Default stock and ETF lists for analysis
DEFAULT_TICKERS = {
    'large_cap_tech': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'ADBE', 'CRM'
    ],
    'blue_chip': [
        'AAPL', 'MSFT', 'JNJ', 'JPM', 'PG', 'KO', 'PFE', 'VZ', 'HD', 'WMT'
    ],
    'growth_stocks': [
        'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'NFLX', 'SHOP', 'SQ', 'ROKU', 'ZM'
    ],
    'dividend_stocks': [
        'JNJ', 'PG', 'KO', 'PFE', 'VZ', 'T', 'XOM', 'CVX', 'IBM', 'MMM', "VYM"
    ],
    'etfs_broad_market': [
        'SPY', 'VOO', 'IVV', 'VTI', 'ITOT', 'SPDW', 'VXUS', 'VEA', 'VWO', 'IEFA'
    ],
    'etfs_sector': [
        'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLU', 'XLP', 'XLY', 'XLB', 'XLRE'
    ],
    'crypto_related': [
        'COIN', 'MSTR', 'SQ', 'PYPL', 'RIOT', 'MARA', 'GLXY', 'BITF', 'HUT', 'CLSK'
    ],
    'minerals': [
        'IAU'
    ]
}

# Algorithm configuration
ALGORITHM_CONFIG = {
    'default_price_weight': 0.6,
    'default_sentiment_weight': 0.4,
    'min_headlines_for_sentiment': 2,
    'sentiment_lookback_days': 7,
    'price_momentum_period': 1,  # days
    'normalization_method': 'minmax',  # 'minmax' or 'zscore'
    'version': '1.0'
}

# Risk management settings
RISK_MANAGEMENT = {
    'max_portfolio_risk_per_trade': 0.02,  # 2%
    'max_position_size': 0.10,  # 10% of portfolio
    'max_daily_trades': 10,
    'max_daily_loss': 0.05,  # 5% of portfolio
    'default_stop_loss': 0.05,  # 5%
    'default_take_profit': 0.15,  # 15%
    'correlation_threshold': 0.7
}

# Data source configuration
DATA_SOURCES = {
    'primary_market_data': 'yahoo',  # 'yahoo', 'alpha_vantage'
    'news_source': 'finviz',  # 'finviz', 'finnhub'
    'sentiment_model': 'vader',  # 'vader', 'finbert'
    'rate_limit_delay': 0.2,  # seconds between API calls
    'retry_attempts': 3,
    'timeout_seconds': 30
}

# Database configuration
DATABASE_CONFIG = {
    'default_db_type': 'sqlite',
    'sqlite_path': '../data/investment_framework.db',
    'connection_pool_size': 5,
    'connection_pool_recycle': 3600,  # 1 hour
    'query_timeout': 30,
    'echo_sql': False
}

# Dashboard configuration
DASHBOARD_CONFIG = {
    'default_port': 8501,
    'theme': 'light',
    'cache_ttl_seconds': 300,  # 5 minutes
    'max_tickers_per_analysis': 50,
    'default_chart_height': 400,
    'update_frequency_options': ['5min', '15min', '30min', '1hour', 'manual']
}

# Trading configuration
TRADING_CONFIG = {
    'default_paper_trading': True,
    'default_investment_amount': 1000,
    'min_trade_amount': 100,
    'max_trade_amount': 10000,
    'order_timeout_seconds': 60,
    'bracket_order_enabled': True
}

# Logging configuration
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': '../logs/framework.log',
    'max_log_size_mb': 10,
    'backup_count': 5,
    'console_logging': True
}

# News sentiment configuration
SENTIMENT_CONFIG = {
    'max_headlines_per_stock': 20,
    'sentiment_boost_threshold': 0.05,
    'financial_keywords_weight': 0.1,
    'headline_min_length': 10,
    'exclude_keywords': ['earnings', 'dividend', 'split'],  # Neutral news types
    'positive_keywords': [
        'bullish', 'gains', 'surge', 'rally', 'outperform', 'beat', 'exceed',
        'strong', 'growth', 'profit', 'revenue', 'upgrade', 'buy', 'positive',
        'momentum', 'breakthrough', 'expansion', 'acquisition', 'dividend',
        'innovation', 'partnership', 'launch', 'success', 'record', 'milestone'
    ],
    'negative_keywords': [
        'bearish', 'losses', 'decline', 'crash', 'underperform', 'miss', 'below',
        'weak', 'loss', 'deficit', 'downgrade', 'sell', 'negative', 'concern',
        'lawsuit', 'investigation', 'bankruptcy', 'recession', 'volatility',
        'warning', 'risk', 'threat', 'challenge', 'issue', 'problem', 'delay'
    ]
}

# Technical analysis configuration
TECHNICAL_CONFIG = {
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'ma_short_period': 10,
    'ma_long_period': 50,
    'volume_ma_period': 20,
    'volatility_period': 30,
    'momentum_period': 12
}

# Performance monitoring
MONITORING_CONFIG = {
    'track_api_performance': True,
    'track_algorithm_performance': True,
    'alert_on_errors': True,
    'performance_log_interval': 3600,  # 1 hour
    'health_check_interval': 300,  # 5 minutes
    'max_error_rate': 0.1  # 10%
}

# Email/notification configuration (optional)
NOTIFICATION_CONFIG = {
    'email_enabled': False,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email_subject_prefix': '[Investment Framework]',
    'daily_summary_enabled': False,
    'alert_thresholds': {
        'high_score': 85,
        'portfolio_loss': 0.05,
        'system_error': True
    }
}

# API rate limits and quotas
API_LIMITS = {
    'alpha_vantage': {
        'calls_per_minute': 5,
        'calls_per_day': 500
    },
    'polygon': {
        'calls_per_minute': 5,
        'calls_per_day': 1000
    },
    'finnhub': {
        'calls_per_minute': 60,
        'calls_per_day': 1000
    },
    'yahoo_finance': {
        'calls_per_minute': 100,  # Generally more lenient
        'calls_per_day': 10000
    }
}


def get_config() -> Dict[str, Any]:
    """
    Get complete configuration dictionary with environment variable overrides
    
    Returns:
        Dictionary containing all configuration settings
    """
    config = {
        'tickers': DEFAULT_TICKERS,
        'algorithm': ALGORITHM_CONFIG,
        'risk_management': RISK_MANAGEMENT,
        'data_sources': DATA_SOURCES,
        'database': DATABASE_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'trading': TRADING_CONFIG,
        'logging': LOGGING_CONFIG,
        'sentiment': SENTIMENT_CONFIG,
        'technical': TECHNICAL_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'notifications': NOTIFICATION_CONFIG,
        'api_limits': API_LIMITS
    }
    
    # Override with environment variables where applicable
    config['algorithm']['default_price_weight'] = float(
        os.getenv('PRICE_WEIGHT', config['algorithm']['default_price_weight'])
    )
    config['algorithm']['default_sentiment_weight'] = float(
        os.getenv('SENTIMENT_WEIGHT', config['algorithm']['default_sentiment_weight'])
    )
    
    config['risk_management']['max_portfolio_risk_per_trade'] = float(
        os.getenv('RISK_PERCENTAGE', config['risk_management']['max_portfolio_risk_per_trade'])
    )
    
    config['logging']['log_level'] = os.getenv('LOG_LEVEL', config['logging']['log_level'])
    
    config['trading']['default_paper_trading'] = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    
    config['data_sources']['primary_market_data'] = os.getenv(
        'PRIMARY_DATA_SOURCE', config['data_sources']['primary_market_data']
    )
    
    return config


def get_default_tickers(category: str = 'large_cap_tech') -> List[str]:
    """
    Get default ticker list for a specific category
    
    Args:
        category: Category of tickers to return
        
    Returns:
        List of ticker symbols
    """
    return DEFAULT_TICKERS.get(category, DEFAULT_TICKERS['large_cap_tech'])


def get_risk_settings(conservative: bool = True) -> Dict[str, float]:
    """
    Get risk management settings
    
    Args:
        conservative: Whether to use conservative settings
        
    Returns:
        Dictionary with risk settings
    """
    if conservative:
        return {
            'max_portfolio_risk_per_trade': 0.01,  # 1%
            'max_position_size': 0.05,  # 5%
            'max_daily_trades': 5,
            'max_daily_loss': 0.03,  # 3%
            'default_stop_loss': 0.03,  # 3%
            'default_take_profit': 0.10,  # 10%
        }
    else:
        return RISK_MANAGEMENT


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration settings
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if configuration is valid
    """
    try:
        # Check algorithm weights sum to 1
        price_weight = config['algorithm']['default_price_weight']
        sentiment_weight = config['algorithm']['default_sentiment_weight']
        
        if abs(price_weight + sentiment_weight - 1.0) > 0.001:
            raise ValueError("Price and sentiment weights must sum to 1.0")
        
        # Check risk percentages are reasonable
        if config['risk_management']['max_portfolio_risk_per_trade'] > 0.1:
            raise ValueError("Portfolio risk per trade should not exceed 10%")
        
        if config['risk_management']['max_position_size'] > 0.5:
            raise ValueError("Maximum position size should not exceed 50%")
        
        # Check that required fields exist
        required_fields = [
            'algorithm', 'risk_management', 'data_sources', 
            'database', 'trading', 'logging'
        ]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required configuration field missing: {field}")
        
        return True
        
    except Exception as e:
        print(f"Configuration validation error: {e}")
        return False


if __name__ == "__main__":
    # Test configuration
    config = get_config()
    
    if validate_config(config):
        print("✅ Configuration is valid")
        print(f"Algorithm weights: {config['algorithm']['default_price_weight']:.1%} price, "
              f"{config['algorithm']['default_sentiment_weight']:.1%} sentiment")
        print(f"Risk settings: {config['risk_management']['max_portfolio_risk_per_trade']:.1%} max risk per trade")
        print(f"Default tickers: {len(get_default_tickers())} symbols")
    else:
        print("❌ Configuration validation failed")
