"""
Risk Management Module

This module provides comprehensive risk management functionality including
position sizing, portfolio management, and trade validation.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """
    Comprehensive risk management system for algorithmic trading
    """
    
    def __init__(self, 
                 max_portfolio_risk: float = 0.02,
                 max_position_size: float = 0.10,
                 max_daily_trades: int = 10,
                 max_daily_loss: float = 0.05,
                 correlation_threshold: float = 0.7):
        """
        Initialize risk manager with configuration parameters
        
        Args:
            max_portfolio_risk: Maximum portfolio risk per trade (2%)
            max_position_size: Maximum position size as % of portfolio (10%)
            max_daily_trades: Maximum number of trades per day
            max_daily_loss: Maximum daily loss as % of portfolio (5%)
            correlation_threshold: Maximum correlation between positions (0.7)
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_size = max_position_size
        self.max_daily_trades = max_daily_trades
        self.max_daily_loss = max_daily_loss
        self.correlation_threshold = correlation_threshold
        
        # Tracking variables
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.trade_log = []
        self.last_reset_date = datetime.now().date()
        
        logger.info(f"Risk Manager initialized with max risk: {max_portfolio_risk:.1%}, "
                   f"max position: {max_position_size:.1%}")
    
    def reset_daily_counters(self):
        """Reset daily counters if it's a new trading day"""
        current_date = datetime.now().date()
        
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
            logger.info("Daily risk counters reset for new trading day")
    
    def calculate_position_size(self, 
                               account_value: float,
                               entry_price: float,
                               stop_loss_price: float,
                               risk_amount: Optional[float] = None) -> int:
        """
        Calculate optimal position size based on risk management rules
        
        Args:
            account_value: Total account value
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            risk_amount: Specific risk amount (optional)
            
        Returns:
            Number of shares to trade
        """
        if entry_price <= 0 or account_value <= 0:
            return 0
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share <= 0:
            logger.warning("Invalid stop loss price, using default 5% risk")
            risk_per_share = entry_price * 0.05
        
        # Determine risk amount
        if risk_amount is None:
            risk_amount = account_value * self.max_portfolio_risk
        
        # Calculate shares based on risk
        shares_by_risk = int(risk_amount / risk_per_share)
        
        # Apply position size limit
        max_position_value = account_value * self.max_position_size
        shares_by_position_limit = int(max_position_value / entry_price)
        
        # Take the minimum for safety
        final_shares = min(shares_by_risk, shares_by_position_limit)
        
        logger.info(f"Position sizing: Risk-based: {shares_by_risk}, "
                   f"Position limit: {shares_by_position_limit}, "
                   f"Final: {final_shares}")
        
        return max(0, final_shares)
    
    def validate_trade(self, 
                      trade_request: Dict,
                      current_positions: List[Dict],
                      account_value: float) -> Tuple[bool, str]:
        """
        Validate a trade request against risk management rules
        
        Args:
            trade_request: Dictionary with trade details
            current_positions: List of current positions
            account_value: Current account value
            
        Returns:
            Tuple of (is_valid, reason)
        """
        self.reset_daily_counters()
        
        symbol = trade_request.get('symbol', '')
        action = trade_request.get('action', '')
        quantity = trade_request.get('quantity', 0)
        price = trade_request.get('price', 0)
        
        # Basic validation
        if not symbol or not action or quantity <= 0 or price <= 0:
            return False, "Invalid trade parameters"
        
        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"
        
        # Check daily loss limit
        if self.daily_pnl < -account_value * self.max_daily_loss:
            return False, f"Daily loss limit reached ({self.max_daily_loss:.1%})"
        
        # For buy orders, check additional constraints
        if action.lower() == 'buy':
            # Check position size limit
            position_value = quantity * price
            position_percentage = position_value / account_value
            
            if position_percentage > self.max_position_size:
                return False, f"Position too large ({position_percentage:.1%} > {self.max_position_size:.1%})"
            
            # Check for existing position in same symbol
            existing_position = next((pos for pos in current_positions if pos['symbol'] == symbol), None)
            if existing_position:
                current_value = abs(existing_position['market_value'])
                total_value = current_value + position_value
                total_percentage = total_value / account_value
                
                if total_percentage > self.max_position_size:
                    return False, f"Combined position too large ({total_percentage:.1%})"
            
            # Check correlation with existing positions
            correlation_risk = self._check_correlation_risk(symbol, current_positions)
            if correlation_risk:
                return False, f"High correlation risk with existing positions"
        
        return True, "Trade approved"
    
    def update_daily_pnl(self, pnl_change: float):
        """Update daily P&L tracking"""
        self.daily_pnl += pnl_change
        logger.info(f"Daily P&L updated: {self.daily_pnl:.2f}")
    
    def record_trade(self, trade_details: Dict):
        """Record a completed trade"""
        self.daily_trades += 1
        
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': trade_details.get('symbol'),
            'action': trade_details.get('action'),
            'quantity': trade_details.get('quantity'),
            'price': trade_details.get('price'),
            'daily_trade_count': self.daily_trades
        }
        
        self.trade_log.append(trade_record)
        
        # Keep only last 100 trades
        if len(self.trade_log) > 100:
            self.trade_log = self.trade_log[-100:]
        
        logger.info(f"Trade recorded: {trade_details.get('action')} {trade_details.get('quantity')} "
                   f"{trade_details.get('symbol')} @ ${trade_details.get('price'):.2f}")
    
    def calculate_portfolio_risk(self, positions: List[Dict], account_value: float) -> Dict:
        """
        Calculate overall portfolio risk metrics
        
        Args:
            positions: List of current positions
            account_value: Total account value
            
        Returns:
            Dictionary with risk metrics
        """
        if not positions or account_value <= 0:
            return {
                'total_exposure': 0.0,
                'largest_position_pct': 0.0,
                'number_of_positions': 0,
                'concentration_risk': 'Low',
                'diversification_score': 100
            }
        
        # Calculate position metrics
        position_values = [abs(pos['market_value']) for pos in positions]
        total_exposure = sum(position_values)
        largest_position = max(position_values)
        
        largest_position_pct = largest_position / account_value
        exposure_pct = total_exposure / account_value
        
        # Assess concentration risk
        if largest_position_pct > 0.25:
            concentration_risk = 'High'
        elif largest_position_pct > 0.15:
            concentration_risk = 'Medium'
        else:
            concentration_risk = 'Low'
        
        # Simple diversification score (based on number of positions and concentration)
        num_positions = len(positions)
        diversification_score = min(100, (num_positions * 10) - (largest_position_pct * 100))
        
        return {
            'total_exposure': exposure_pct,
            'largest_position_pct': largest_position_pct,
            'number_of_positions': num_positions,
            'concentration_risk': concentration_risk,
            'diversification_score': max(0, diversification_score),
            'position_values': position_values
        }
    
    def suggest_rebalancing(self, positions: List[Dict], target_weights: Dict = None) -> List[Dict]:
        """
        Suggest portfolio rebalancing actions
        
        Args:
            positions: Current positions
            target_weights: Target allocation weights (optional)
            
        Returns:
            List of suggested rebalancing actions
        """
        suggestions = []
        
        if not positions:
            return suggestions
        
        # Calculate current weights
        total_value = sum(abs(pos['market_value']) for pos in positions)
        
        for position in positions:
            symbol = position['symbol']
            current_value = abs(position['market_value'])
            current_weight = current_value / total_value
            
            # Check if position is too large
            if current_weight > self.max_position_size:
                excess_weight = current_weight - self.max_position_size
                excess_value = excess_weight * total_value
                
                suggestions.append({
                    'action': 'reduce',
                    'symbol': symbol,
                    'current_weight': current_weight,
                    'target_weight': self.max_position_size,
                    'excess_value': excess_value,
                    'reason': 'Position too large'
                })
        
        return suggestions
    
    def _check_correlation_risk(self, symbol: str, current_positions: List[Dict]) -> bool:
        """
        Check if adding a symbol would create correlation risk
        
        Args:
            symbol: Symbol to check
            current_positions: Current positions
            
        Returns:
            True if high correlation risk exists
        """
        # Simplified correlation check based on sector/industry
        # In a production system, you would use historical price correlations
        
        # Define sector groupings for basic correlation check
        sector_groups = {
            'tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA'],
            'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C'],
            'etf_large': ['SPY', 'VOO', 'IVV', 'VTI'],
            'etf_tech': ['QQQ', 'XLK', 'VGT'],
            'retail': ['WMT', 'TGT', 'COST', 'HD', 'LOW']
        }
        
        # Find which group the symbol belongs to
        symbol_group = None
        for group, tickers in sector_groups.items():
            if symbol in tickers:
                symbol_group = group
                break
        
        if not symbol_group:
            return False  # Unknown symbol, no correlation risk
        
        # Count positions in the same group
        same_group_count = 0
        for position in current_positions:
            pos_symbol = position['symbol']
            if pos_symbol in sector_groups[symbol_group]:
                same_group_count += 1
        
        # Risk if we already have 3+ positions in the same group
        return same_group_count >= 3
    
    def get_risk_summary(self, account_value: float, positions: List[Dict]) -> Dict:
        """
        Get comprehensive risk summary
        
        Args:
            account_value: Total account value
            positions: Current positions
            
        Returns:
            Dictionary with risk summary
        """
        self.reset_daily_counters()
        
        portfolio_risk = self.calculate_portfolio_risk(positions, account_value)
        
        # Calculate remaining daily capacity
        remaining_trades = max(0, self.max_daily_trades - self.daily_trades)
        daily_loss_used = abs(self.daily_pnl) / account_value if account_value > 0 else 0
        remaining_loss_capacity = max(0, self.max_daily_loss - daily_loss_used)
        
        return {
            'portfolio_risk': portfolio_risk,
            'daily_metrics': {
                'trades_used': self.daily_trades,
                'trades_remaining': remaining_trades,
                'daily_pnl': self.daily_pnl,
                'daily_loss_used_pct': daily_loss_used,
                'remaining_loss_capacity_pct': remaining_loss_capacity
            },
            'risk_limits': {
                'max_portfolio_risk': self.max_portfolio_risk,
                'max_position_size': self.max_position_size,
                'max_daily_trades': self.max_daily_trades,
                'max_daily_loss': self.max_daily_loss
            },
            'last_updated': datetime.now()
        }


# Factory function for easy instantiation
def create_risk_manager(conservative: bool = True) -> RiskManager:
    """
    Factory function to create a RiskManager instance
    
    Args:
        conservative: Whether to use conservative risk settings
        
    Returns:
        RiskManager instance
    """
    if conservative:
        return RiskManager(
            max_portfolio_risk=0.01,  # 1% risk per trade
            max_position_size=0.05,   # 5% max position
            max_daily_trades=5,       # 5 trades per day
            max_daily_loss=0.03       # 3% daily loss limit
        )
    else:
        return RiskManager(
            max_portfolio_risk=0.02,  # 2% risk per trade
            max_position_size=0.10,   # 10% max position
            max_daily_trades=10,      # 10 trades per day
            max_daily_loss=0.05       # 5% daily loss limit
        )


if __name__ == "__main__":
    # Example usage
    risk_manager = create_risk_manager(conservative=True)
    
    # Example portfolio
    account_value = 100000
    positions = [
        {'symbol': 'AAPL', 'market_value': 5000},
        {'symbol': 'MSFT', 'market_value': 4000},
        {'symbol': 'SPY', 'market_value': 3000}
    ]
    
    # Get risk summary
    risk_summary = risk_manager.get_risk_summary(account_value, positions)
    
    print("Risk Summary:")
    print(f"  Total Exposure: {risk_summary['portfolio_risk']['total_exposure']:.1%}")
    print(f"  Largest Position: {risk_summary['portfolio_risk']['largest_position_pct']:.1%}")
    print(f"  Concentration Risk: {risk_summary['portfolio_risk']['concentration_risk']}")
    print(f"  Daily Trades Used: {risk_summary['daily_metrics']['trades_used']}")
    
    # Test trade validation
    trade_request = {
        'symbol': 'GOOGL',
        'action': 'buy',
        'quantity': 10,
        'price': 150.0
    }
    
    is_valid, reason = risk_manager.validate_trade(trade_request, positions, account_value)
    print(f"\nTrade Validation: {'✅ Approved' if is_valid else '❌ Rejected'} - {reason}")
