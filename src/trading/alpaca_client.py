"""
Alpaca Trading Client Module

This module provides integration with the Alpaca trading API for executing
trades based on the algorithmic ranking system.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
import time

from dotenv import load_dotenv

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest, LimitOrderRequest, StopLossRequest, 
        TakeProfitRequest, GetOrdersRequest
    )
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, OrderStatus
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca library not installed. Trading functionality will be limited.")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlpacaTradingClient:
    """
    Wrapper class for Alpaca trading operations with built-in risk management
    """
    
    def __init__(self, paper_trading: bool = True):
        """
        Initialize Alpaca trading client
        
        Args:
            paper_trading: Whether to use paper trading (default: True for safety)
        """
    # Supports TASK-015: Alpaca client wrapper using paper trading keys from .env
        if not ALPACA_AVAILABLE:
            raise ImportError("Alpaca library not installed. Install with: pip install alpaca-py")
        
        self.paper_trading = paper_trading
        
        # Get API credentials
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        base_url = os.getenv('ALPACA_BASE_URL')
        
        if not all([api_key, secret_key]):
            raise ValueError("Alpaca API credentials not found. Please set ALPACA_API_KEY and ALPACA_SECRET_KEY")
        
        # Set base URL based on paper trading mode
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = "https://paper-api.alpaca.markets" if paper_trading else "https://api.alpaca.markets"
        
        # Initialize clients
        try:
            self.trading_client = TradingClient(api_key, secret_key, paper=paper_trading)
            self.data_client = StockHistoricalDataClient(api_key, secret_key)
            
            # Test connection
            account = self.trading_client.get_account()
            logger.info(f"Connected to Alpaca {'Paper' if paper_trading else 'Live'} Trading")
            logger.info(f"Account Status: {account.status}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca API: {e}")
            raise
        
    # Risk management settings
    # Supports TASK-018: Default stop-loss/take-profit parameters
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', '0.02'))  # 2% of portfolio
        self.default_stop_loss_pct = float(os.getenv('DEFAULT_STOP_LOSS', '0.05'))  # 5%
        self.default_take_profit_pct = float(os.getenv('DEFAULT_TAKE_PROFIT', '0.15'))  # 15%
        
        logger.info(f"Risk Management - Max Position: {self.max_position_size:.1%}, "
                   f"Stop Loss: {self.default_stop_loss_pct:.1%}, "
                   f"Take Profit: {self.default_take_profit_pct:.1%}")
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            
            return {
                'account_id': account.id,
                'status': account.status,
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'cash': float(account.cash),
                'equity': float(account.equity),
                'last_equity': float(account.last_equity),
                'day_trade_count': account.daytrade_count,
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            
            position_list = []
            for position in positions:
                position_dict = {
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'side': position.side,
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'current_price': float(position.current_price),
                    'avg_entry_price': float(position.avg_entry_price)
                }
                position_list.append(position_dict)
            
            return position_list
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def calculate_position_size(self, symbol: str, current_price: float, 
                              risk_amount: Optional[float] = None) -> int:
        """
        Calculate appropriate position size based on risk management rules
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            risk_amount: Amount willing to risk (default: max_position_size of portfolio)
            
        Returns:
            Number of shares to buy
        """
        try:
            account = self.get_account_info()
            portfolio_value = account.get('portfolio_value', 0)
            
            if portfolio_value == 0:
                logger.warning("Portfolio value is 0, cannot calculate position size")
                return 0
            
            # Use provided risk amount or default percentage of portfolio
            if risk_amount is None:
                risk_amount = portfolio_value * self.max_position_size
            
            # Calculate shares based on risk amount
            max_shares_by_risk = int(risk_amount / current_price)
            
            # Additional check: don't exceed 10% of portfolio in any single position
            max_shares_by_concentration = int((portfolio_value * 0.1) / current_price)
            
            # Take the minimum for safety
            shares = min(max_shares_by_risk, max_shares_by_concentration)
            
            logger.info(f"Position size calculation for {symbol}: "
                       f"Price: ${current_price:.2f}, "
                       f"Risk amount: ${risk_amount:.2f}, "
                       f"Calculated shares: {shares}")
            
            return max(0, shares)  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def place_market_order(self, symbol: str, side: str, qty: int,
                          take_profit_pct: Optional[float] = None,
                          stop_loss_pct: Optional[float] = None) -> Optional[str]:
        """
        Place a market order with optional bracket orders
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Number of shares
            take_profit_pct: Take profit percentage (optional)
            stop_loss_pct: Stop loss percentage (optional)
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            if qty <= 0:
                logger.warning(f"Invalid quantity {qty} for {symbol}")
                return None
            
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            
            # Basic market order
            if not take_profit_pct and not stop_loss_pct:
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
                )
            else:
                # Bracket order with take profit and/or stop loss
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=TimeInForce.GTC,  # Good till cancelled for bracket orders
                    order_class=OrderClass.BRACKET
                )
                
                # Add take profit if specified
                if take_profit_pct:
                    # Get current price to calculate take profit price
                    current_price = self._get_current_price(symbol)
                    if current_price:
                        if side.lower() == 'buy':
                            tp_price = current_price * (1 + take_profit_pct)
                        else:
                            tp_price = current_price * (1 - take_profit_pct)
                        
                        order_request.take_profit = TakeProfitRequest(
                            limit_price=round(tp_price, 2)
                        )
                
                # Add stop loss if specified
                if stop_loss_pct:
                    current_price = self._get_current_price(symbol)
                    if current_price:
                        if side.lower() == 'buy':
                            sl_price = current_price * (1 - stop_loss_pct)
                        else:
                            sl_price = current_price * (1 + stop_loss_pct)
                        
                        order_request.stop_loss = StopLossRequest(
                            stop_price=round(sl_price, 2)
                        )
            
            # Submit order
            order = self.trading_client.submit_order(order_request)
            
            logger.info(f"Order submitted: {order.id} - {side.upper()} {qty} shares of {symbol}")
            
            if take_profit_pct or stop_loss_pct:
                logger.info(f"Bracket order with TP: {take_profit_pct}, SL: {stop_loss_pct}")
            
            return order.id
            
        except Exception as e:
            logger.error(f"Error placing {side} order for {symbol}: {e}")
            return None
    
    def place_limit_order(self, symbol: str, side: str, qty: int, limit_price: float) -> Optional[str]:
        """
        Place a limit order
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Number of shares
            limit_price: Limit price for the order
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
            
            order = self.trading_client.submit_order(order_request)
            
            logger.info(f"Limit order submitted: {order.id} - {side.upper()} {qty} shares of {symbol} at ${limit_price:.2f}")
            
            return order.id
            
        except Exception as e:
            logger.error(f"Error placing limit order for {symbol}: {e}")
            return None
    
    def get_orders(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get orders with optional status filter
        
        Args:
            status: Order status filter (e.g., 'open', 'closed', 'all')
            limit: Maximum number of orders to return
            
        Returns:
            List of order dictionaries
        """
        try:
            if status:
                if status.lower() == 'open':
                    order_status = OrderStatus.NEW
                elif status.lower() == 'closed':
                    order_status = OrderStatus.FILLED
                else:
                    order_status = None
            else:
                order_status = None
            
            request = GetOrdersRequest(
                status=order_status,
                limit=limit
            )
            
            orders = self.trading_client.get_orders(request)
            
            order_list = []
            for order in orders:
                order_dict = {
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'side': order.side,
                    'order_type': order.order_type,
                    'status': order.status,
                    'submitted_at': order.submitted_at,
                    'filled_at': order.filled_at,
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
                }
                
                if hasattr(order, 'limit_price') and order.limit_price:
                    order_dict['limit_price'] = float(order.limit_price)
                
                order_list.append(order_dict)
            
            return order_list
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Use the data client to get recent price
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(days=1)
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if symbol in bars.data and len(bars.data[symbol]) > 0:
                latest_bar = bars.data[symbol][-1]
                return float(latest_bar.close)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def execute_ranking_based_trade(self, rankings_df, top_n: int = 3, 
                                   investment_amount: float = 1000) -> List[Dict]:
        """
        Execute trades based on ranking results
        
        Args:
            rankings_df: DataFrame with asset rankings
            top_n: Number of top assets to consider for buying
            investment_amount: Total amount to invest across positions
            
        Returns:
            List of trade execution results
        """
        results = []
        
        try:
            # Get account info
            account_info = self.get_account_info()
            available_cash = account_info.get('cash', 0)
            
            if available_cash < investment_amount:
                logger.warning(f"Insufficient cash: ${available_cash:.2f} < ${investment_amount:.2f}")
                investment_amount = available_cash * 0.9  # Use 90% of available cash
            
            # Get top picks
            top_picks = rankings_df.head(top_n)
            amount_per_position = investment_amount / len(top_picks)
            
            logger.info(f"Executing trades for top {top_n} assets with ${amount_per_position:.2f} each")
            
            for _, asset in top_picks.iterrows():
                symbol = asset['ticker']
                price = asset['price']
                score = asset['composite_score']
                
                if price is None or price <= 0:
                    logger.warning(f"Invalid price for {symbol}, skipping")
                    continue
                
                # Calculate position size
                shares = int(amount_per_position / price)
                
                if shares <= 0:
                    logger.warning(f"Cannot afford even 1 share of {symbol} at ${price:.2f}")
                    continue
                
                # Determine take profit and stop loss based on score
                if score >= 80:  # High confidence
                    take_profit_pct = self.default_take_profit_pct * 1.2  # 20% higher target
                    stop_loss_pct = self.default_stop_loss_pct * 0.8      # Tighter stop
                elif score >= 65:  # Medium confidence
                    take_profit_pct = self.default_take_profit_pct
                    stop_loss_pct = self.default_stop_loss_pct
                else:  # Lower confidence
                    take_profit_pct = self.default_take_profit_pct * 0.8  # Lower target
                    stop_loss_pct = self.default_stop_loss_pct * 1.2      # Wider stop
                
                # Place order
                order_id = self.place_market_order(
                    symbol=symbol,
                    side='buy',
                    qty=shares,
                    take_profit_pct=take_profit_pct,
                    stop_loss_pct=stop_loss_pct
                )
                
                result = {
                    'symbol': symbol,
                    'action': 'buy',
                    'shares': shares,
                    'price': price,
                    'score': score,
                    'order_id': order_id,
                    'take_profit_pct': take_profit_pct,
                    'stop_loss_pct': stop_loss_pct,
                    'timestamp': datetime.now(),
                    'success': order_id is not None
                }
                
                results.append(result)
                
                # Rate limiting
                time.sleep(1)
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing ranking-based trades: {e}")
            return []


# Factory function for easy instantiation
def create_alpaca_client(paper_trading: bool = True) -> Optional[AlpacaTradingClient]:
    """
    Factory function to create an AlpacaTradingClient instance
    
    Args:
        paper_trading: Whether to use paper trading (default: True)
        
    Returns:
        AlpacaTradingClient instance or None if setup fails
    """
    try:
        return AlpacaTradingClient(paper_trading=paper_trading)
    except Exception as e:
        logger.error(f"Failed to create Alpaca client: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    client = create_alpaca_client(paper_trading=True)
    
    if client:
        # Get account info
        account_info = client.get_account_info()
        print(f"Account Status: {account_info.get('status', 'Unknown')}")
        print(f"Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        print(f"Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
        
        # Get positions
        positions = client.get_positions()
        if positions:
            print(f"\nCurrent Positions ({len(positions)}):")
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']:.2f} "
                      f"(P&L: ${pos['unrealized_pl']:.2f})")
        else:
            print("\nNo current positions")
        
        # Get recent orders
        orders = client.get_orders(limit=5)
        if orders:
            print(f"\nRecent Orders ({len(orders)}):")
            for order in orders:
                print(f"  {order['symbol']}: {order['side']} {order['qty']} @ {order['status']}")
    else:
        print("Failed to create Alpaca client. Check your API credentials.")
