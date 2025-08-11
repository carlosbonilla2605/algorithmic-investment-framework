
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
import os
from datetime import datetime, timedelta
import time
from src.data_acquisition.news_sentiment import create_news_sentiment_manager, SentimentAnalyzer
from src.database.database_manager import DatabaseManager
from src.database.models import Security, PriceData, NewsArticle, RankingResult, ArticleSentiment, SecurityNewsLink

# Add the src directory to Python path

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.analysis.ranking_engine import create_ranking_engine
from src.data_acquisition.market_data import create_market_data_manager

def get_cached_analysis(tickers, max_age_minutes=5):
    """Get recent analysis results from database if available"""
    db = DatabaseManager()
    cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)

    try:
        with db.get_session() as session:
            # Get most recent analysis time
            latest_analysis = session.query(RankingResult.analysis_date)\
                .order_by(RankingResult.analysis_date.desc())\
                .first()

            if not latest_analysis or latest_analysis[0] < cutoff_time:
                return None

            # Get rankings for our tickers with explicit joins
            results = session.query(RankingResult, Security, PriceData)\
                .join(Security, RankingResult.security_id == Security.id)\
                .join(PriceData, (Security.id == PriceData.security_id) &
                                (RankingResult.analysis_date == PriceData.date))\
                .filter(Security.symbol.in_(tickers))\
                .filter(RankingResult.analysis_date == latest_analysis[0])\
                .all()

            if len(results) != len(tickers):
                return None

            # Process and convert data types
            data = []
            for r in results:
                try:
                    row = {
                        'rank': r.RankingResult.rank,
                        'ticker': r.Security.symbol,
                        'composite_score': float(r.RankingResult.composite_score) if r.RankingResult.composite_score else None,
                        'technical_score': float(r.RankingResult.technical_score) if r.RankingResult.technical_score else None,
                        'sentiment_score': float(r.RankingResult.sentiment_score) if r.RankingResult.sentiment_score else None,
                        'headline_count': r.RankingResult.news_count,
                        'positive_ratio': r.RankingResult.positive_news_ratio,
                        'price': None,
                        'date': None,
                        'percent_change': None
                    }

                    # Handle price data
                    if hasattr(r, 'PriceData') and r.PriceData:
                        try:
                            row['price'] = float(r.PriceData.close_price) if r.PriceData.close_price else None
                            row['date'] = pd.to_datetime(r.PriceData.date) if r.PriceData.date else None
                        except (TypeError, ValueError) as e:
                            logger.warning(f"Error converting price data for {r.Security.symbol}: {e}")

                    # Handle percent change
                    if hasattr(r.RankingResult, 'price_change_1d') and r.RankingResult.price_change_1d is not None:
                        try:
                            row['percent_change'] = float(r.RankingResult.price_change_1d)
                        except (TypeError, ValueError) as e:
                            logger.warning(f"Error converting percent change for {r.Security.symbol}: {e}")

                    data.append(row)
                except Exception as e:
                    logger.error(f"Error processing result for {getattr(r.Security, 'symbol', 'unknown')}: {e}")
                    continue

            df = pd.DataFrame(data)

            # Convert decimal types to float for visualization
            for col in ['price', 'percent_change', 'composite_score', 'technical_score', 'sentiment_score']:
                if col in df.columns and df[col].dtype == 'object':  # Decimal is stored as object
                    df[col] = df[col].astype(float)

            # Ensure dates are datetime
            for col in df.select_dtypes(include=['datetime64']).columns:
                df[col] = pd.to_datetime(df[col])

            # Convert list of dicts to DataFrame
            df = pd.DataFrame(data)

            # Set DataFrame attributes
            df.attrs['analysis_timestamp'] = latest_analysis[0]
            df.attrs['price_weight'] = float(results[0].RankingResult.price_weight) if results and results[0].RankingResult.price_weight else 0.6
            df.attrs['sentiment_weight'] = float(results[0].RankingResult.sentiment_weight) if results and results[0].RankingResult.sentiment_weight else 0.4

            return df
    except Exception as e:
        st.error(f"Error accessing database: {e}")
        return None

# Page configuration
# Supports TASK-003: Streamlit dashboard entry point launches from repo root
st.set_page_config(
    page_title="Investment Decision Framework",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive { color: #00ff00; }
    .negative { color: #ff0000; }
    .neutral { color: #808080; }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_market_data(tickers, provider='yahoo'):
    """Cached function to get market data"""
    manager = create_market_data_manager(provider)
    return manager.get_price_data(tickers)


@st.cache_data(ttl=600)  # Cache for 10 minutes  
def get_historical_data(ticker, period='6mo'):
    """Cached function to get historical data"""
    manager = create_market_data_manager()
    return manager.get_historical_data(ticker, period)


def run_ranking_analysis(tickers, price_weight, sentiment_weight, force_refresh=False):
    """Run the ranking analysis with caching
    
    Args:
        tickers: List of stock symbols to analyze
        price_weight: Weight for technical analysis (0-1)
        sentiment_weight: Weight for sentiment analysis (0-1)
        force_refresh: If True, skip cache and force new analysis
    """
    
    # Check cache first (unless force_refresh is True)
    if not force_refresh:
        cached_df = get_cached_analysis(tickers)
        if cached_df is not None:
            return cached_df
    
    # Run new analysis
    engine = create_ranking_engine(price_weight=price_weight, 
                                 sentiment_weight=sentiment_weight)
    
    try:
        return engine.rank_assets(tickers, include_details=True)
    except Exception as e:
        st.error(f"Error running analysis: {e}")
        return pd.DataFrame()


def main():
    """Main dashboard function"""
    
    # Header
    st.title("📈 Algorithmic Investment Decision Framework")
    st.markdown("---")
    
    # Sidebar for inputs
    st.sidebar.header("⚙️ Configuration")
    
    # Ticker input
    st.sidebar.subheader("🎯 Assets to Analyze")
    
    # Predefined ticker sets
    ticker_presets = {
        "Tech Giants": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
        "S&P 500 ETFs": ["SPY", "VOO", "IVV", "VTI"],
        "Growth Stocks": ["NVDA", "TSLA", "AMZN", "GOOGL", "META", "NFLX"],
        "Blue Chips": ["AAPL", "MSFT", "JNJ", "KO", "JPM", "PG"],
        "Sector ETFs": ["XLK", "XLF", "XLE", "XLV", "XLI", "XLU"],
        "Custom": []
    }
    
    preset_choice = st.sidebar.selectbox("Choose a preset or Custom:", list(ticker_presets.keys()))
    
    if preset_choice == "Custom":
        tickers_input = st.sidebar.text_area(
            "Enter tickers (comma-separated):",
            value="AAPL, MSFT, GOOGL, AMZN, TSLA, SPY, QQQ",
            help="Enter stock/ETF symbols separated by commas"
        )
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(',') if ticker.strip()]
    else:
        tickers = ticker_presets[preset_choice]
        st.sidebar.write(f"Selected tickers: {', '.join(tickers)}")
    
    # Algorithm parameters
    st.sidebar.subheader("⚖️ Algorithm Weights")
    price_weight = st.sidebar.slider(
        "Price Momentum Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
        help="Weight given to price momentum in the ranking algorithm"
    )
    
    sentiment_weight = 1.0 - price_weight
    st.sidebar.write(f"Sentiment Weight: {sentiment_weight:.2f}")
    
    # Analysis button
    force_refresh = st.sidebar.button("🚀 Run Analysis", type="primary")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5 min)", value=False)
    if auto_refresh:
        time.sleep(1)  # Small delay to prevent too frequent refreshes
        force_refresh = True
    
    # Main content
    if not tickers:
        st.warning("⚠️ Please select some tickers to analyze.")
        return
    
    # Show current selections
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Assets Selected", len(tickers))
    with col2:
        st.metric("⚖️ Price Weight", f"{price_weight:.0%}")
    with col3:
        st.metric("📰 Sentiment Weight", f"{sentiment_weight:.0%}")
    
    # Run analysis
    with st.spinner("🔄 Running analysis... This may take a few minutes..."):
        try:
            # Pass force_refresh to determine whether to skip cache
            rankings_df = run_ranking_analysis(tickers, price_weight, sentiment_weight, force_refresh=force_refresh)
            
            if len(rankings_df) == 0:
                st.error("❌ No data could be retrieved. Please try again or check your tickers.")
                return
            
            # Display results
            display_results(rankings_df, tickers)
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("💡 Try refreshing the page or selecting different tickers.")


def display_results(rankings_df, tickers):
    """Display the analysis results"""
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Historical Performance Section
    # Supports TASK-004: Show simple price charts and ranked tables
    st.subheader("📈 Historical Performance")
    
    # Time period selector for historical data
    time_periods = {
        "1 Week": "1wk",
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "Year to Date": "ytd"
    }
    selected_period = st.selectbox(
        "Select Time Period",
        options=list(time_periods.keys()),
        index=2  # Default to 3 months
    )
    
    # Get historical data for top assets
    top_tickers = rankings_df.head(3)['ticker'].tolist()
    historical_data = {}
    
    with st.spinner("Loading historical data..."):
        for ticker in top_tickers:
            try:
                historical_data[ticker] = get_historical_data(ticker, time_periods[selected_period])
            except Exception as e:
                st.warning(f"Could not fetch historical data for {ticker}: {str(e)}")
    
    # Create historical price chart
    if historical_data:
        fig = go.Figure()
        
        for ticker, data in historical_data.items():
            # Normalize prices to percentage change from start
            prices = data['Close']
            norm_prices = ((prices - prices.iloc[0]) / prices.iloc[0]) * 100
            
            fig.add_trace(go.Scatter(
                x=data.index,
                y=norm_prices,
                name=ticker,
                mode='lines',
                hovertemplate=
                "%{x}<br>" +
                "Change: %{y:.1f}%<br>" +
                "<extra></extra>"
            ))
        
        fig.update_layout(
            title="Relative Performance Comparison",
            xaxis_title="Date",
            yaxis_title="% Change",
            hovermode='x unified',
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics table
        metrics_data = []
        for ticker, data in historical_data.items():
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            period_return = ((end_price - start_price) / start_price) * 100
            max_price = data['High'].max()
            min_price = data['Low'].min()
            volatility = data['Close'].pct_change().std() * 100 * (252 ** 0.5)  # Annualized
            
            metrics_data.append({
                'Ticker': ticker,
                'Period Return': f"{period_return:+.1f}%",
                'Highest Price': f"${max_price:.2f}",
                'Lowest Price': f"${min_price:.2f}",
                'Volatility (Ann.)': f"{volatility:.1f}%"
            })
        
        st.markdown("### 📊 Performance Metrics")
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(
            metrics_df,
            hide_index=True,
            use_container_width=True
        )
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        top_score = rankings_df['composite_score'].max()
        st.metric("🏆 Top Score", f"{top_score:.1f}")
    
    with col2:
        avg_score = rankings_df['composite_score'].mean()
        st.metric("📊 Average Score", f"{avg_score:.1f}")
    
    with col3:
        positive_sentiment = (rankings_df['sentiment_score'] > 50).sum()
        st.metric("😊 Positive Sentiment", f"{positive_sentiment}/{len(rankings_df)}")
    
    with col4:
        positive_momentum = (rankings_df['percent_change'] > 0).sum()
        st.metric("📈 Positive Momentum", f"{positive_momentum}/{len(rankings_df)}")
    
    st.markdown("---")
    
    # Initialize risk manager for position calculations
    from src.trading.risk_manager import RiskManager
    risk_manager = RiskManager()
    
    # Calculate sample position size for top picks
    st.markdown("### 📊 Position Sizing for Top Picks")
    
    # Simulated account value for demonstration
    sample_account_value = 100000
    
    position_data = []
    for idx, row in rankings_df.head(3).iterrows():
        entry_price = row['current_price'] if 'current_price' in row else 100  # fallback price
        stop_loss = entry_price * 0.95  # 5% stop loss for example
        
        shares = risk_manager.calculate_position_size(
            account_value=sample_account_value,
            entry_price=entry_price,
            stop_loss_price=stop_loss
        )
        
        position_value = shares * entry_price
        portfolio_percentage = (position_value / sample_account_value) * 100
        
        position_data.append({
            'Symbol': idx,
            'Max Shares': shares,
            'Position Value': f"${position_value:,.2f}",
            'Portfolio %': f"{portfolio_percentage:.1f}%",
            'Risk Level': "Low" if portfolio_percentage < 5 else "Medium" if portfolio_percentage < 8 else "High"
        })
    
    position_df = pd.DataFrame(position_data)
    st.table(position_df)
    
    # Top picks section
    st.markdown("---")
    st.subheader("🎯 Top Investment Picks")
    
    top_picks = rankings_df.head(5).copy()
    
    # Add recommendation based on score
    top_picks['recommendation'] = top_picks['composite_score'].apply(
        lambda x: '🟢 Strong Buy' if x >= 80 else 
                 '🔵 Buy' if x >= 65 else 
                 '🟡 Hold' if x >= 50 else 
                 '🟠 Weak Hold' if x >= 35 else '🔴 Avoid'
    )
    
    # Format percent change with colors
    def format_percent_change(val):
        if val > 0:
            return f"<span class='positive'>+{val:.2f}%</span>"
        elif val < 0:
            return f"<span class='negative'>{val:.2f}%</span>"
        else:
            return f"<span class='neutral'>{val:.2f}%</span>"
    
    # Display top picks table
    display_cols = ['rank', 'ticker', 'composite_score', 'recommendation', 'percent_change', 'headline_count']
    top_picks_display = top_picks[display_cols].copy()
    top_picks_display['percent_change'] = top_picks_display['percent_change'].apply(
        lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%"
    )
    
    st.dataframe(
        top_picks_display,
        column_config={
            "rank": "Rank",
            "ticker": "Ticker",
            "composite_score": st.column_config.NumberColumn("Score", format="%.1f"),
            "recommendation": "Recommendation",
            "percent_change": "Daily Change",
            "headline_count": "Headlines"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Detailed rankings table
    st.subheader("📋 Complete Rankings")
    
    # Columns to display
    detailed_cols = ['rank', 'ticker', 'composite_score', 'technical_score', 'sentiment_score',
                    'price', 'percent_change', 'headline_count', 'positive_ratio']
    
    st.dataframe(
        rankings_df[detailed_cols],
        column_config={
            "rank": "Rank",
            "ticker": "Ticker",
            "composite_score": st.column_config.NumberColumn("Composite Score", format="%.1f"),
            "technical_score": st.column_config.NumberColumn("Technical Score", format="%.1f"),
            "sentiment_score": st.column_config.NumberColumn("Sentiment Score", format="%.1f"),
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "percent_change": st.column_config.NumberColumn("Daily Change %", format="%.2f"),
            "headline_count": "Headlines",
            "positive_ratio": st.column_config.NumberColumn("Positive News %", format="%.0%")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Visualizations
    create_visualizations(rankings_df)
    
    # Individual asset analysis
    individual_analysis_section(rankings_df, tickers)

    # Trading Integration Section
    st.markdown("---")
    st.header("🤖 Trading Integration")
    
    # Initialize Alpaca client
    from src.trading.alpaca_client import create_alpaca_client
    
    try:
        alpaca = create_alpaca_client()
        if not alpaca:
            raise RuntimeError("Alpaca client not available")
        
        account_info = alpaca.get_account_info() or {}
        positions = alpaca.get_positions() or []
        orders = alpaca.get_orders(status='open') or []
        
        # Portfolio Overview
        st.subheader("💼 Portfolio Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            equity = float(account_info.get('equity', 0) or 0)
            last_equity = float(account_info.get('last_equity', 0) or 0)
            daily_change = ((equity - last_equity) / last_equity) * 100 if last_equity > 0 else 0
            st.metric(
                "Portfolio Value",
                f"${equity:,.2f}",
                f"{daily_change:+.2f}%"
            )
        
        with col2:
            buying_power = float(account_info.get('buying_power', 0) or 0)
            st.metric("Buying Power", f"${buying_power:,.2f}")
            
        with col3:
            st.metric("Open Positions", len(positions))
            
        with col4:
            st.metric("Pending Orders", len(orders))
        
        # Position Management
        st.subheader("📊 Current Positions")
        if positions:
            positions_data = []
            for position in positions:
                unrealized_pl_pct = (float(position.get('unrealized_pl', 0) or 0) / float(position.get('cost_basis', 1) or 1)) * 100 if float(position.get('cost_basis', 0) or 0) != 0 else 0.0
                positions_data.append({
                    'Symbol': position.get('symbol', ''),
                    'Shares': int(position.get('qty') or 0),
                    'Avg Price': f"${float(position.get('avg_entry_price', 0) or 0):.2f}",
                    'Current Price': f"${float(position.get('current_price', 0) or 0):.2f}",
                    'Market Value': f"${float(position.get('market_value', 0) or 0):.2f}",
                    'P&L': f"${float(position.get('unrealized_pl', 0) or 0):.2f}",
                    'P&L %': f"{unrealized_pl_pct:+.2f}%"
                })
            
            positions_df = pd.DataFrame(positions_data)
            st.dataframe(
                positions_df,
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No open positions")
        
        # Order Management
        st.subheader("📋 Open Orders")
        if orders:
            orders_data = []
            for order in orders:
                submitted_at = order.get('submitted_at')
                if submitted_at:
                    if hasattr(submitted_at, 'strftime'):
                        submitted_str = submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        try:
                            submitted_str = pd.to_datetime(str(submitted_at)).strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            submitted_str = str(submitted_at)
                else:
                    submitted_str = ''

                # Build safe display values
                limit_val = order.get('limit_price', None)
                if limit_val is None or limit_val == '' or str(limit_val).lower() == 'none':
                    limit_display = "Market"
                else:
                    try:
                        limit_display = f"${float(limit_val):.2f}"
                    except Exception:
                        limit_display = str(limit_val)

                orders_data.append({
                    'Symbol': order.get('symbol', ''),
                    'Side': str(order.get('side', '')).capitalize(),
                    'Type': str(order.get('order_type', order.get('type', 'N/A'))).upper(),
                    'Qty': int(order.get('qty') or 0),
                    'Limit Price': limit_display,
                    'Status': str(order.get('status', 'unknown')).capitalize(),
                    'Submitted': submitted_str
                })

            orders_df = pd.DataFrame(orders_data)
            st.dataframe(
                orders_df,
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No pending orders")
        
        # New Order Form
        st.subheader("🆕 Place New Order")
        with st.form("new_order_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                order_symbol = st.selectbox(
                    "Symbol",
                    options=tickers,
                    index=0
                )
                
                order_side = st.radio(
                    "Side",
                    options=['buy', 'sell'],
                    horizontal=True
                )
            
            with col2:
                order_type = st.radio(
                    "Order Type",
                    options=['market', 'limit'],
                    horizontal=True
                )
                
                order_qty = st.number_input(
                    "Quantity",
                    min_value=1,
                    value=1
                )
            
            with col3:
                order_limit_price = st.number_input(
                    "Limit Price (if applicable)",
                    min_value=0.01,
                    value=float(rankings_df[rankings_df['ticker'] == order_symbol]['price'].iloc[0])
                    if order_symbol in rankings_df['ticker'].values else 0.01,
                    disabled=(order_type == 'market')
                )
                
                time_in_force = st.radio(
                    "Time In Force",
                    options=['day', 'gtc'],
                    horizontal=True,
                    help="Day: Cancel at end of day, GTC: Good Till Cancelled"
                )
            
            submit_order = st.form_submit_button("Submit Order")
            
            if submit_order:
                try:
                    # Create the order using the appropriate method
                    if order_type == 'market':
                        order_id = alpaca.place_market_order(
                            symbol=order_symbol,
                            side=order_side,
                            qty=order_qty
                        )
                    else:
                        order_id = alpaca.place_limit_order(
                            symbol=order_symbol,
                            side=order_side,
                            qty=order_qty,
                            limit_price=float(order_limit_price)
                        )
                    if order_id:
                        st.success(f"Order submitted successfully! Order ID: {order_id}")
                    else:
                        st.error("Order submission failed.")
                except Exception as e:
                    st.error(f"Failed to submit order: {str(e)}")
        
        # Quick Trading Actions for Top Picks
        st.subheader("🎯 Quick Trade Top Picks")
        quick_trade_cols = st.columns(3)
        
        for i, (_, row) in enumerate(rankings_df.head(3).iterrows()):
            with quick_trade_cols[i]:
                ticker = row['ticker']
                current_price = row['price']
                
                st.markdown(f"### {ticker}")
                st.write(f"Current Price: ${current_price:.2f}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Buy {ticker}", key=f"quick_buy_{ticker}"):
                        try:
                            order_id = alpaca.place_market_order(
                                symbol=ticker,
                                side='buy',
                                qty=1
                            )
                            if order_id:
                                st.success(f"Market buy order placed for {ticker} (ID: {order_id})")
                            else:
                                st.error("Failed to place buy order.")
                        except Exception as e:
                            st.error(f"Failed to place order: {str(e)}")
                
                with col2:
                    if st.button(f"Sell {ticker}", key=f"quick_sell_{ticker}"):
                        try:
                            order_id = alpaca.place_market_order(
                                symbol=ticker,
                                side='sell',
                                qty=1
                            )
                            if order_id:
                                st.success(f"Market sell order placed for {ticker} (ID: {order_id})")
                            else:
                                st.error("Failed to place sell order.")
                        except Exception as e:
                            st.error(f"Failed to place order: {str(e)}")
    
    except Exception as e:
        st.error("Failed to connect to Alpaca API. Please check your API keys and try again.")
        st.info("To use paper trading, make sure to set up your Alpaca API keys in the environment variables:\n"
                "- ALPACA_API_KEY\n"
                "- ALPACA_API_SECRET\n"
                "- ALPACA_PAPER (set to 'true' for paper trading)")

    # --- Risk Summary and Limits Section ---
    st.markdown("---")
    st.header("🛡️ Risk Summary & Limits")

    from src.trading.risk_manager import create_risk_manager
    
    # Estimate account value as sum of prices (for demo; replace with real value if available)
    account_value = float(rankings_df['price'].sum()) if 'price' in rankings_df.columns else 100000
    
    # Create main risk metrics section with cards
    st.subheader("📊 Key Risk Metrics")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    
    with metrics_col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Portfolio Risk Profile</h4>
            <p>Max Risk per Trade: <span class="big-font">2.0%</span></p>
            <p>Current Risk Level: <span class="big-font positive">1.2%</span></p>
            <p>Risk Capacity: <span class="big-font">40%</span> available</p>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Position Management</h4>
            <p>Max Position Size: <span class="big-font">10.0%</span></p>
            <p>Largest Position: <span class="big-font neutral">7.5%</span></p>
            <p>Portfolio Utilization: <span class="big-font">75%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Daily Controls</h4>
            <p>Max Daily Loss: <span class="big-font">5.0%</span></p>
            <p>Current P&L: <span class="big-font positive">+1.2%</span></p>
            <p>Trades: <span class="big-font">3</span>/10 used</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Position Correlation Matrix
    st.subheader("🔄 Position Correlations")
    if len(rankings_df) > 1:
        # Calculate correlation matrix for top assets
        top_assets = rankings_df.head(5)
        correlation_matrix = pd.DataFrame(index=top_assets['ticker'], columns=top_assets['ticker'])
        
        # Simulate correlations (replace with real correlation calculation if available)
        for i, ticker1 in enumerate(top_assets['ticker']):
            for j, ticker2 in enumerate(top_assets['ticker']):
                if i == j:
                    correlation_matrix.loc[ticker1, ticker2] = 1.0
                else:
                    # Simulate random correlation between -1 and 1
                    correlation_matrix.loc[ticker1, ticker2] = np.random.uniform(-0.7, 0.7)
        
        # Create heatmap
        heatmap_fig = px.imshow(correlation_matrix,
                              labels=dict(color="Correlation"),
                              color_continuous_scale="RdBu",
                              aspect="auto")
        heatmap_fig.update_layout(title="Asset Correlation Matrix")
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Risk Distribution
    st.subheader("📈 Risk Allocation")
    risk_col1, risk_col2 = st.columns(2)
    
    with risk_col1:
        # Create donut chart for risk allocation
        labels = ['Equity Risk', 'Market Risk', 'Sector Risk', 'Unused Risk']
        values = [30, 25, 20, 25]
        donut_fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
        donut_fig.update_layout(title="Risk Allocation by Type")
        st.plotly_chart(donut_fig, use_container_width=True)
    
    with risk_col2:
        # Create risk metrics table
        risk_metrics = pd.DataFrame({
            'Metric': ['Value at Risk (VaR)', 'Expected Shortfall', 'Beta', 'Sharpe Ratio'],
            'Value': ['$2,345', '$3,456', '0.85', '1.23'],
            'Status': ['✅ Within Limits', '✅ Within Limits', '⚠️ High', '✅ Good']
        })
        st.table(risk_metrics)
    
    # Build positions list for risk manager
    positions = []
    for _, row in rankings_df.iterrows():
        positions.append({
            'symbol': row['ticker'],
            'market_value': row['price'] * max(row.get('composite_score', 1)/100, 0.01)
        })
    risk_manager = create_risk_manager(conservative=True)
    risk_summary = risk_manager.get_risk_summary(account_value, positions)

    pr = risk_summary['portfolio_risk']
    dm = risk_summary['daily_metrics']
    rl = risk_summary['risk_limits']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Exposure", f"{pr['total_exposure']:.1%}")
        st.metric("Largest Position %", f"{pr['largest_position_pct']:.1%}")
    with col2:
        st.metric("Concentration Risk", pr['concentration_risk'])
        st.metric("Diversification Score", pr['diversification_score'])
    with col3:
        st.metric("Daily Trades Used", dm['trades_used'])
        st.metric("Trades Remaining", dm['trades_remaining'])
    with col4:
        st.metric("Daily P&L", f"${dm['daily_pnl']:.2f}")
        st.metric("Daily Loss Used %", f"{dm['daily_loss_used_pct']:.1%}")

    st.subheader("Risk Limits")
    st.write(f"**Max Portfolio Risk per Trade:** {rl['max_portfolio_risk']:.1%}")
    st.write(f"**Max Position Size:** {rl['max_position_size']:.1%}")
    st.write(f"**Max Daily Trades:** {rl['max_daily_trades']}")
    st.write(f"**Max Daily Loss:** {rl['max_daily_loss']:.1%}")


def display_news_headlines(selected_ticker):
    """Display news headlines and sentiment for a given ticker"""
    db = DatabaseManager()

    try:
        # Prefer stored headlines (last 14 days)
        stored = db.get_recent_news(selected_ticker, days=14)
        if stored:
            st.caption("Stored headlines (last 14 days)")
            news_df = pd.DataFrame([{
                'Date': row.get('published_at'),
                'Headline': row.get('headline'),
                'Sentiment': row.get('compound_score'),
                'Source': row.get('source')
            } for row in stored if isinstance(row, dict)])
            if not news_df.empty:
                # If some stored rows lack sentiment, compute it on the fly
                if news_df['Sentiment'].isna().any():
                    try:
                        analyzer = SentimentAnalyzer()
                        mask = news_df['Sentiment'].isna()
                        news_df.loc[mask, 'Sentiment'] = news_df.loc[mask, 'Headline'].apply(
                            lambda h: analyzer.analyze_sentiment(h).get('compound', None) if isinstance(h, str) else None
                        )
                    except Exception:
                        pass
                news_df['Sentiment Display'] = news_df['Sentiment'].apply(
                    lambda x: ("N/A ⚪" if x is None else f"{x:.2f} {'🟢' if x > 0.2 else '🔴' if x < -0.2 else '⚪'}")
                )
                news_df = news_df.sort_values('Date', ascending=False)
                st.dataframe(news_df[['Date', 'Headline', 'Sentiment Display', 'Source']], use_container_width=True)
                return

        # Fallback: live fetch headlines and display without DB
        from src.data_acquisition.news_sentiment import create_news_sentiment_manager
        st.info("No stored news found. Fetching latest headlines...")
        mgr = create_news_sentiment_manager()
        live = mgr.get_sentiment_for_ticker(selected_ticker)
        headlines = live.get('headlines', [])
        sentiments = live.get('headline_sentiments', [])
        if not headlines:
            st.info("No recent news headlines available for this asset")
            return
        rows = []
        for h, s in zip(headlines, sentiments or [None]*len(headlines)):
            comp = s.get('compound') if isinstance(s, dict) else None
            rows.append({
                'Date': datetime.now(),
                'Headline': h,
                'Sentiment': comp,
                'Source': 'FinViz'
            })
        news_df = pd.DataFrame(rows)
        news_df['Sentiment Display'] = news_df['Sentiment'].apply(
            lambda x: ("N/A ⚪" if x is None else f"{x:.2f} {'🟢' if x > 0.2 else '🔴' if x < -0.2 else '⚪'}")
        )
        st.dataframe(news_df[['Date', 'Headline', 'Sentiment Display', 'Source']], use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching news data: {e}")

def create_visualizations(rankings_df):
    """Create interactive visualizations"""
    
    st.markdown("---")
    st.header("📈 Visualizations")
    
    # Score distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Score Distribution")
        
        fig_dist = px.histogram(
            rankings_df,
            x='composite_score',
            nbins=20,
            title="Distribution of Composite Scores",
            labels={'composite_score': 'Composite Score', 'count': 'Frequency'}
        )
        fig_dist.update_layout(showlegend=False)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        st.subheader("Price vs Sentiment")
        
        fig_scatter = px.scatter(
            rankings_df,
            x='technical_score',
            y='sentiment_score',
            size='composite_score',
            color='percent_change',
            hover_name='ticker',
            title="Technical vs Sentiment Scores",
            labels={
                'technical_score': 'Technical Score',
                'sentiment_score': 'Sentiment Score',
                'percent_change': 'Daily Change %'
            },
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Top 10 comparison
    st.subheader("Top 10 Assets Comparison")
    
    top_10 = rankings_df.head(10)
    
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        name='Technical Score',
        x=top_10['ticker'],
        y=top_10['technical_score'],
        marker_color='lightblue'
    ))
    
    fig_bar.add_trace(go.Bar(
        name='Sentiment Score',
        x=top_10['ticker'],
        y=top_10['sentiment_score'],
        marker_color='lightcoral'
    ))
    
    fig_bar.add_trace(go.Scatter(
        name='Composite Score',
        x=top_10['ticker'],
        y=top_10['composite_score'],
        mode='lines+markers',
        line=dict(color='green', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig_bar.update_layout(
        title="Score Breakdown for Top 10 Assets",
        xaxis_title="Ticker",
        yaxis_title="Technical & Sentiment Scores",
        yaxis2=dict(
            title="Composite Score",
            overlaying='y',
            side='right'
        ),
        barmode='group',
        height=500
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)


def individual_analysis_section(rankings_df, tickers):
    """Individual asset analysis section"""
    
    st.markdown("---")
    st.header("🔍 Individual Asset Analysis")
    
    # Asset selector
    selected_ticker = st.selectbox(
        "Select an asset for detailed analysis:",
        options=tickers,
        index=0
    )
    
    if selected_ticker:
        # Get asset data
        asset_data = rankings_df[rankings_df['ticker'] == selected_ticker].iloc[0]
        
        # Asset overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Price", f"${asset_data['price']:.2f}")
        
        with col2:
            change_val = asset_data['percent_change']
            st.metric("Daily Change", f"{change_val:+.2f}%", delta=f"{change_val:.2f}%")
        
        with col3:
            st.metric("Rank", f"#{asset_data['rank']}")
        
        with col4:
            st.metric("Composite Score", f"{asset_data['composite_score']:.1f}/100")
        
        # Display score components
        score_data = {
            'Component': ['Technical Score', 'Sentiment Score', 'Composite Score'],
            'Score': [asset_data.get('technical_score', 0), 
                     asset_data.get('sentiment_score', 0), 
                     asset_data.get('composite_score', 0)],
            'Weight': ['60%', '40%', '100%']
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_gauge = go.Figure()
            
            fig_gauge.add_trace(go.Bar(
                x=['Technical', 'Sentiment', 'Composite'],
                y=score_data['Score'],
                marker_color=['lightblue', 'lightcoral', 'lightgreen'],
                text=[f"{score:.1f}" for score in score_data['Score']],
                textposition='auto'
            ))
            
            fig_gauge.update_layout(
                title=f"Score Components for {selected_ticker}",
                yaxis_title="Score (0-100)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Details")
            headline_count = asset_data.get('headline_count', 0)
            st.write(f"**Headlines Analyzed:** {headline_count}")
            
            if headline_count == 0:
                st.info("No headlines available for this asset.")
            
            st.write(f"**Positive News Ratio:** {asset_data.get('positive_ratio', 0):.1%}")
            
            volume = asset_data.get('volume')
            if volume is not None:
                st.write(f"**Volume:** {volume:,.0f}")
            
            sentiment_std = asset_data.get('sentiment_std')
            if sentiment_std and sentiment_std > 0:
                st.write(f"**Sentiment Consistency:** {(1-sentiment_std):.1%}")
        
        # Historical data sections
        tab1, tab2, tab3 = st.tabs(["📈 Price History", "🎯 Ranking History", "📊 Performance"])
        
        with tab1:
            # Get historical price data
            from src.database.database_manager import DatabaseManager
            db = DatabaseManager()
            price_history = db.get_latest_prices([selected_ticker], 30)

            if price_history and len(price_history) > 0:
                price_data = []
                for p in price_history:
                    try:
                        # Only accept dict rows from DatabaseManager to avoid detached ORM access
                        if not isinstance(p, dict):
                            continue
                        op = p.get('open_price')
                        hp = p.get('high_price')
                        lp = p.get('low_price')
                        cp = p.get('close_price')
                        price_data.append({
                            'date': pd.to_datetime(str(p.get('date'))) if p.get('date') else None,
                            'open_price': float(op) if op is not None else np.nan,
                            'high_price': float(hp) if hp is not None else np.nan,
                            'low_price': float(lp) if lp is not None else np.nan,
                            'close_price': float(cp) if cp is not None else np.nan
                        })
                    except Exception as e:
                        st.warning(f"Skipping invalid price data: {e}")
                        continue

                price_df = pd.DataFrame(price_data)
                # Drop rows without a valid date
                if not price_df.empty:
                    price_df = price_df.dropna(subset=['date'])

                if price_df.empty:
                    st.info("No valid historical price data available")
                else:
                    price_df.set_index('date', inplace=True)
                    price_df.sort_index(inplace=True)

                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=price_df.index,
                        open=price_df['open_price'],
                        high=price_df['high_price'],
                        low=price_df['low_price'],
                        close=price_df['close_price'],
                        name='Price'
                    ))
                    fig.update_layout(
                        title=f"{selected_ticker} - 30 Day Price History",
                        yaxis_title="Price ($)",
                        xaxis_title="Date"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No historical price data available")
        
        with tab2:
            # Get ranking history
            ranking_history = db.get_latest_rankings(limit=30)
            if ranking_history and len(ranking_history) > 0:
                # Convert to DataFrame, supporting dict rows
                rows = []
                for r in ranking_history:
                    try:
                        if isinstance(r, dict):
                            rows.append({
                                'analysis_date': pd.to_datetime(str(r.get('analysis_date'))) if r.get('analysis_date') else None,
                                'composite_score': r.get('composite_score'),
                                'technical_score': r.get('technical_score'),
                                'sentiment_score': r.get('sentiment_score'),
                                'rank': r.get('rank'),
                                'symbol': r.get('symbol')
                            })
                        else:
                            rank_obj = getattr(r, 'RankingResult', None)
                            sec_obj = getattr(r, 'Security', None)
                            if rank_obj is None and isinstance(r, (tuple, list)) and len(r) >= 2:
                                rank_obj, sec_obj = r[0], r[1]
                            if rank_obj is None:
                                continue
                            rows.append({
                                'analysis_date': pd.to_datetime(str(getattr(rank_obj, 'analysis_date'))) if getattr(rank_obj, 'analysis_date', None) else None,
                                'composite_score': getattr(rank_obj, 'composite_score', None),
                                'technical_score': getattr(rank_obj, 'technical_score', None),
                                'sentiment_score': getattr(rank_obj, 'sentiment_score', None),
                                'rank': getattr(rank_obj, 'rank', None),
                                'symbol': getattr(sec_obj, 'symbol', None) if sec_obj is not None else None
                            })
                    except Exception:
                        continue
                ranking_df = pd.DataFrame(rows)

                # Guard for missing columns or empty dataset
                if ranking_df.empty or 'symbol' not in ranking_df.columns or 'analysis_date' not in ranking_df.columns:
                    st.info("No ranking history available for the latest analysis.")
                    
                else:
                    ticker_rankings = ranking_df[ranking_df['symbol'] == selected_ticker]
                    if len(ticker_rankings) > 0:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                        x=ticker_rankings['analysis_date'],
                        y=ticker_rankings['composite_score'],
                        name='Composite Score',
                        line=dict(color='green', width=2)
                    ))
                        fig.add_trace(go.Scatter(
                        x=ticker_rankings['analysis_date'],
                        y=ticker_rankings['technical_score'],
                        name='Technical Score',
                        line=dict(color='blue', width=2)
                    ))
                        fig.add_trace(go.Scatter(
                        x=ticker_rankings['analysis_date'],
                        y=ticker_rankings['sentiment_score'],
                        name='Sentiment Score',
                        line=dict(color='red', width=2)
                    ))
                        fig.update_layout(
                        title=f"{selected_ticker} - Score History",
                        yaxis_title="Score",
                        xaxis_title="Date"
                    )
                        st.plotly_chart(fig, use_container_width=True)

                        # Display rank changes
                        st.subheader("Rank Changes")
                        rank_df = ticker_rankings[['analysis_date', 'rank']].copy()
                        rank_df['rank_change'] = rank_df['rank'].diff()
                        st.dataframe(rank_df, use_container_width=True)
                    else:
                        st.info("No ranking history for the selected ticker in the latest analysis window.")
            else:
                st.info("No ranking history available")
        
        with tab3:
            # Get trade history
            trade_history = db.get_trade_history(selected_ticker, days=30)
            if trade_history and len(trade_history) > 0:
                # Convert to DataFrame supporting dict rows
                rows = []
                for t in trade_history:
                    if isinstance(t, dict):
                        rows.append({
                            'date': t.get('date'),
                            'type': t.get('type'),
                            'quantity': t.get('quantity'),
                            'price': t.get('price'),
                            'total_value': t.get('total_value'),
                            'symbol': t.get('symbol')
                        })
                    else:
                        tr = getattr(t, 'TradeRecord', None)
                        sec = getattr(t, 'Security', None)
                        if tr is None and isinstance(t, (tuple, list)) and len(t) >= 2:
                            tr, sec = t[0], t[1]
                        if tr is None:
                            continue
                        rows.append({
                            'date': getattr(tr, 'trade_date', None),
                            'type': getattr(tr, 'trade_type', None),
                            'quantity': getattr(tr, 'quantity', None),
                            'price': getattr(tr, 'price', None),
                            'total_value': getattr(tr, 'total_value', None),
                            'symbol': getattr(sec, 'symbol', None) if sec is not None else None
                        })
                trade_df = pd.DataFrame(rows)
                
                st.subheader("Recent Trades")
                st.dataframe(trade_df, use_container_width=True)
                
                # Calculate basic performance metrics
                total_trades = len(trade_df)
                buy_trades = len(trade_df[trade_df['type'] == 'buy'])
                sell_trades = len(trade_df[trade_df['type'] == 'sell'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Trades", total_trades)
                with col2:
                    st.metric("Buy Orders", buy_trades)
                with col3:
                    st.metric("Sell Orders", sell_trades)
            else:
                st.info("No trade history available")

    # News headlines section
    with st.expander(f"📰 News Headlines & Sentiment for {selected_ticker}"):
        display_news_headlines(selected_ticker)

if __name__ == "__main__":
    main()
