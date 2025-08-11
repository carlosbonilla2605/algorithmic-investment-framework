"""
Backtesting Module

This module implements a comprehensive backtesting framework for testing
investment strategies on historical data. It calculates key performance 
metrics including CAGR, Sharpe ratio, and maximum drawdown.

TASK-031: Add a lightweight backtest runner over historical daily data
TASK-032: Report CAGR, Sharpe, and max drawdown
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import time
import warnings

from src.data_acquisition.market_data import MarketDataManager, create_market_data_manager
from src.analysis.ranking_engine import RankingEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class BacktestResult:
    """
    Container for backtesting results and performance metrics
    """
    
    def __init__(self):
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.initial_capital: float = 0.0
        self.final_value: float = 0.0
        self.total_return: float = 0.0
        self.cagr: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.volatility: float = 0.0
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        self.total_trades: int = 0
        self.win_rate: float = 0.0
        
        # Detailed tracking
        self.portfolio_values: List[float] = []
        self.portfolio_dates: List[datetime] = []
        self.trade_history: List[Dict] = []
        self.daily_returns: List[float] = []
        
    def calculate_metrics(self):
        """Calculate performance metrics from portfolio values"""
        if len(self.portfolio_values) < 2:
            logger.warning("Insufficient data to calculate metrics")
            return
            
        # Basic metrics
        self.final_value = self.portfolio_values[-1]
        self.total_return = (self.final_value - self.initial_capital) / self.initial_capital
        
        # Calculate daily returns
        portfolio_series = pd.Series(self.portfolio_values, index=self.portfolio_dates)
        self.daily_returns = portfolio_series.pct_change().dropna().tolist()
        
        if len(self.daily_returns) == 0:
            logger.warning("No daily returns to calculate metrics")
            return
            
        # CAGR calculation
        years = (self.end_date - self.start_date).days / 365.25
        if years > 0:
            self.cagr = (self.final_value / self.initial_capital) ** (1/years) - 1
        
        # Volatility (annualized)
        self.volatility = np.std(self.daily_returns) * np.sqrt(252) if self.daily_returns else 0.0
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        if self.volatility > 0:
            mean_return = np.mean(self.daily_returns) * 252  # Annualized
            self.sharpe_ratio = mean_return / self.volatility
        
        # Maximum Drawdown
        peak = self.portfolio_values[0]
        max_dd = 0.0
        
        for value in self.portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
                
        self.max_drawdown = max_dd
        
        # Trade statistics
        self.total_trades = len(self.trade_history)
        self.winning_trades = sum(1 for trade in self.trade_history if trade.get('return', 0) > 0)
        self.losing_trades = self.total_trades - self.winning_trades
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        
    def summary(self) -> Dict:
        """Return a summary of backtest results"""
        return {
            'Period': f"{self.start_date.strftime('%Y-%m-%d') if self.start_date else 'N/A'} to {self.end_date.strftime('%Y-%m-%d') if self.end_date else 'N/A'}",
            'Initial Capital': f"${self.initial_capital:,.2f}",
            'Final Value': f"${self.final_value:,.2f}",
            'Total Return': f"{self.total_return:.2%}",
            'CAGR': f"{self.cagr:.2%}",
            'Volatility': f"{self.volatility:.2%}",
            'Sharpe Ratio': f"{self.sharpe_ratio:.2f}",
            'Max Drawdown': f"{self.max_drawdown:.2%}",
            'Total Trades': self.total_trades,
            'Win Rate': f"{self.win_rate:.2%}",
            'Winning Trades': self.winning_trades,
            'Losing Trades': self.losing_trades
        }


class Position:
    """
    Represents a position in a security
    """
    
    def __init__(self, ticker: str, shares: float, entry_price: float, entry_date: datetime):
        self.ticker = ticker
        self.shares = shares
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.current_price = entry_price
        self.current_value = shares * entry_price
        
    def update_price(self, new_price: float):
        """Update the current price and value"""
        self.current_price = new_price
        self.current_value = self.shares * new_price
        
    def get_return(self) -> float:
        """Calculate return on this position"""
        return (self.current_price - self.entry_price) / self.entry_price
        
    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        return (self.current_price - self.entry_price) * self.shares


class BacktestingEngine:
    """
    Main backtesting engine that simulates trading strategies over historical data
    """
    
    def __init__(self, 
                 ranking_engine: RankingEngine,
                 initial_capital: float = 100000.0,
                 rebalance_frequency: str = 'monthly',
                 top_n_picks: int = 5,
                 transaction_cost: float = 0.001,  # 0.1% per trade
                 max_position_size: float = 0.20):  # Max 20% per position
        """
        Initialize the backtesting engine
        
        Args:
            ranking_engine: RankingEngine instance to use for rankings
            initial_capital: Starting capital for backtest
            rebalance_frequency: How often to rebalance ('daily', 'weekly', 'monthly')
            top_n_picks: Number of top-ranked assets to hold
            transaction_cost: Transaction cost as a percentage of trade value
            max_position_size: Maximum position size as percentage of portfolio
        """
        self.ranking_engine = ranking_engine
        self.initial_capital = initial_capital
        self.rebalance_frequency = rebalance_frequency
        self.top_n_picks = top_n_picks
        self.transaction_cost = transaction_cost
        self.max_position_size = max_position_size
        
        # Market data manager for historical data
        self.market_data_manager = create_market_data_manager()
        
        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.portfolio_value = initial_capital
        
        logger.info(f"Initialized BacktestingEngine with ${initial_capital:,.2f} capital")
        
    def get_rebalance_dates(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """
        Generate rebalancing dates based on frequency
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            List of rebalancing dates
        """
        dates = []
        current_date = start_date
        
        if self.rebalance_frequency == 'daily':
            delta = timedelta(days=1)
        elif self.rebalance_frequency == 'weekly':
            delta = timedelta(weeks=1)
        elif self.rebalance_frequency == 'monthly':
            delta = timedelta(days=30)  # Approximate monthly
        else:
            raise ValueError(f"Unknown rebalance frequency: {self.rebalance_frequency}")
            
        while current_date <= end_date:
            dates.append(current_date)
            current_date += delta
            
        return dates
        
    def get_historical_rankings(self, 
                              tickers: List[str], 
                              date: datetime) -> Optional[pd.DataFrame]:
        """
        Get rankings for a specific historical date
        
        Args:
            tickers: List of tickers to rank
            date: Date for ranking
            
        Returns:
            DataFrame with rankings or None if insufficient data
        """
        try:
            # For backtesting, we need to simulate what the ranking would have been
            # on that date using only data available up to that point
            
            # Get historical price data up to the date
            historical_data = {}
            for ticker in tickers:
                try:
                    # Get data from 30 days before the date to calculate momentum
                    lookback_date = date - timedelta(days=30)
                    data = self.market_data_manager.get_historical_data(
                        ticker, lookback_date, date
                    )
                    if data is not None and len(data) >= 2:
                        # Calculate basic momentum
                        latest_price = data['Close'].iloc[-1]
                        prev_price = data['Close'].iloc[0]
                        percent_change = (latest_price - prev_price) / prev_price * 100
                        
                        historical_data[ticker] = {
                            'price': latest_price,
                            'percent_change': percent_change,
                            'volume': data['Volume'].iloc[-1] if 'Volume' in data else 0
                        }
                except Exception as e:
                    logger.warning(f"Could not get historical data for {ticker} on {date}: {e}")
                    continue
                    
            if not historical_data:
                return None
                
            # Create a simple ranking based on momentum (for backtesting)
            # In a real scenario, we'd also include sentiment analysis
            rankings = []
            for ticker, data in historical_data.items():
                technical_score = data['percent_change']
                sentiment_score = 0.0  # Neutral sentiment for backtesting
                
                # Simple composite score (can be enhanced)
                composite_score = (0.8 * technical_score + 0.2 * sentiment_score)
                
                rankings.append({
                    'ticker': ticker,
                    'composite_score': composite_score,
                    'technical_score': technical_score,
                    'sentiment_score': sentiment_score,
                    'price': data['price'],
                    'percent_change': data['percent_change']
                })
                
            # Convert to DataFrame and sort by composite score
            df = pd.DataFrame(rankings)
            if not df.empty:
                df = df.sort_values('composite_score', ascending=False).reset_index(drop=True)
                df['rank'] = range(1, len(df) + 1)
                
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical rankings for {date}: {e}")
            return None
            
    def rebalance_portfolio(self, 
                          tickers: List[str], 
                          date: datetime, 
                          current_prices: Dict[str, float]) -> List[Dict]:
        """
        Rebalance portfolio based on current rankings
        
        Args:
            tickers: Available tickers to trade
            date: Current date
            current_prices: Current prices for all tickers
            
        Returns:
            List of trades executed
        """
        trades = []
        
        # Get current rankings
        rankings = self.get_historical_rankings(tickers, date)
        if rankings is None or rankings.empty:
            logger.warning(f"No rankings available for {date}")
            return trades
            
        # Update current portfolio value
        self.update_portfolio_value(current_prices)
        
        # Get top picks
        top_picks = rankings.head(self.top_n_picks)['ticker'].tolist()
        
        # Close positions not in top picks
        positions_to_close = [ticker for ticker in self.positions.keys() 
                             if ticker not in top_picks]
        
        for ticker in positions_to_close:
            if ticker in current_prices:
                trade = self.close_position(ticker, current_prices[ticker], date)
                if trade:
                    trades.append(trade)
        
        # Calculate target allocation for each top pick
        target_allocation = min(self.max_position_size, 1.0 / len(top_picks))
        target_value_per_position = self.portfolio_value * target_allocation
        
        # Open or adjust positions for top picks
        for ticker in top_picks:
            if ticker in current_prices:
                current_price = current_prices[ticker]
                target_shares = target_value_per_position / current_price
                
                current_shares = self.positions[ticker].shares if ticker in self.positions else 0
                shares_diff = target_shares - current_shares
                
                if abs(shares_diff) > 0.01:  # Only trade if meaningful difference
                    trade = self.execute_trade(ticker, shares_diff, current_price, date)
                    if trade:
                        trades.append(trade)
        
        return trades
        
    def execute_trade(self, 
                     ticker: str, 
                     shares: float, 
                     price: float, 
                     date: datetime) -> Optional[Dict]:
        """
        Execute a trade (buy or sell)
        
        Args:
            ticker: Ticker symbol
            shares: Number of shares (positive for buy, negative for sell)
            price: Execution price
            date: Trade date
            
        Returns:
            Trade details or None if trade couldn't be executed
        """
        trade_value = abs(shares * price)
        transaction_cost = trade_value * self.transaction_cost
        
        if shares > 0:  # Buy
            total_cost = trade_value + transaction_cost
            if total_cost > self.cash:
                # Insufficient cash, adjust shares
                available_value = self.cash - transaction_cost
                if available_value <= 0:
                    return None
                shares = available_value / price
                trade_value = shares * price
                total_cost = trade_value + transaction_cost
            
            # Execute buy
            self.cash -= total_cost
            
            if ticker in self.positions:
                # Add to existing position
                old_position = self.positions[ticker]
                total_shares = old_position.shares + shares
                avg_price = ((old_position.shares * old_position.entry_price) + 
                           (shares * price)) / total_shares
                self.positions[ticker] = Position(ticker, total_shares, avg_price, date)
            else:
                # New position
                self.positions[ticker] = Position(ticker, shares, price, date)
                
            trade_type = "BUY"
            
        else:  # Sell
            shares = abs(shares)
            if ticker not in self.positions or self.positions[ticker].shares < shares:
                # Can't sell more than we have
                if ticker in self.positions:
                    shares = self.positions[ticker].shares
                else:
                    return None
            
            # Execute sell
            proceeds = (shares * price) - transaction_cost
            self.cash += proceeds
            
            if ticker in self.positions:
                old_position = self.positions[ticker]
                old_position.shares -= shares
                
                if old_position.shares <= 0.01:  # Close position if negligible shares remain
                    del self.positions[ticker]
                    
            trade_type = "SELL"
        
        # Record trade
        trade = {
            'date': date,
            'ticker': ticker,
            'type': trade_type,
            'shares': shares,
            'price': price,
            'value': trade_value,
            'transaction_cost': transaction_cost,
            'cash_after': self.cash
        }
        
        logger.debug(f"{trade_type} {shares:.2f} shares of {ticker} at ${price:.2f}")
        
        return trade
        
    def close_position(self, ticker: str, price: float, date: datetime) -> Optional[Dict]:
        """
        Close a position completely
        
        Args:
            ticker: Ticker to close
            price: Current price
            date: Date of closure
            
        Returns:
            Trade details or None
        """
        if ticker not in self.positions:
            return None
            
        position = self.positions[ticker]
        return self.execute_trade(ticker, -position.shares, price, date)
        
    def update_portfolio_value(self, current_prices: Dict[str, float]):
        """
        Update portfolio value based on current prices
        
        Args:
            current_prices: Dictionary of current prices
        """
        # Update position values
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                position.update_price(current_prices[ticker])
        
        # Calculate total portfolio value
        positions_value = sum(position.current_value for position in self.positions.values())
        self.portfolio_value = self.cash + positions_value
        
    def run_backtest(self, 
                    tickers: List[str],
                    start_date: Union[str, datetime],
                    end_date: Union[str, datetime]) -> BacktestResult:
        """
        Run a complete backtest over the specified period
        
        Args:
            tickers: List of tickers to include in universe
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            BacktestResult with performance metrics
        """
        # Convert dates if strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        logger.info(f"Universe: {tickers}")
        logger.info(f"Strategy: Top {self.top_n_picks} rebalanced {self.rebalance_frequency}")
        
        # Initialize result
        result = BacktestResult()
        result.start_date = start_date
        result.end_date = end_date
        result.initial_capital = self.initial_capital
        
        # Reset portfolio state
        self.cash = self.initial_capital
        self.positions = {}
        self.portfolio_value = self.initial_capital
        
        # Get rebalancing dates
        rebalance_dates = self.get_rebalance_dates(start_date, end_date)
        
        # Track performance
        all_trades = []
        
        try:
            for i, rebalance_date in enumerate(rebalance_dates):
                if rebalance_date > end_date:
                    break
                    
                logger.info(f"Rebalancing on {rebalance_date} ({i+1}/{len(rebalance_dates)})")
                
                # Get current prices for all tickers
                current_prices = {}
                for ticker in tickers:
                    try:
                        # Get price for this specific date
                        data = self.market_data_manager.get_historical_data(
                            ticker, rebalance_date - timedelta(days=1), rebalance_date
                        )
                        if data is not None and len(data) > 0:
                            current_prices[ticker] = data['Close'].iloc[-1]
                    except Exception as e:
                        logger.warning(f"Could not get price for {ticker} on {rebalance_date}: {e}")
                        continue
                
                if not current_prices:
                    logger.warning(f"No price data available for {rebalance_date}")
                    continue
                
                # Update portfolio value
                self.update_portfolio_value(current_prices)
                
                # Record portfolio value
                result.portfolio_values.append(self.portfolio_value)
                result.portfolio_dates.append(rebalance_date)
                
                # Rebalance portfolio
                trades = self.rebalance_portfolio(tickers, rebalance_date, current_prices)
                all_trades.extend(trades)
                
                # Small delay to avoid overwhelming data providers
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error during backtest execution: {e}")
            raise
        
        # Final portfolio update
        if result.portfolio_dates:
            final_date = result.portfolio_dates[-1]
            logger.info(f"Backtest completed. Final portfolio value: ${self.portfolio_value:,.2f}")
        
        # Store trade history and calculate metrics
        result.trade_history = all_trades
        result.calculate_metrics()
        
        logger.info("Backtest Results:")
        for key, value in result.summary().items():
            logger.info(f"  {key}: {value}")
        
        return result


def create_backtesting_engine(ranking_engine: RankingEngine = None, **kwargs) -> BacktestingEngine:
    """
    Factory function to create a BacktestingEngine instance
    
    Args:
        ranking_engine: RankingEngine instance (will create default if None)
        **kwargs: Additional arguments for BacktestingEngine
        
    Returns:
        BacktestingEngine instance
    """
    if ranking_engine is None:
        from src.analysis.ranking_engine import create_ranking_engine
        ranking_engine = create_ranking_engine()
    
    return BacktestingEngine(ranking_engine, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Example backtest
    from src.analysis.ranking_engine import create_ranking_engine
    
    # Create engines
    ranking_engine = create_ranking_engine()
    backtest_engine = create_backtesting_engine(ranking_engine)
    
    # Run a simple backtest
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    try:
        result = backtest_engine.run_backtest(tickers, start_date, end_date)
        
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        for key, value in result.summary().items():
            print(f"{key:20}: {value}")
        print("="*50)
        
    except Exception as e:
        print(f"Backtest failed: {e}")