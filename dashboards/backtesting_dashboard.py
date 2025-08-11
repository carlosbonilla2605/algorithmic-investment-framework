"""
Backtesting Dashboard Component

This module provides Streamlit dashboard components for running and visualizing
backtests of investment strategies.

TASK-031: Add a lightweight backtest runner over historical daily data
TASK-032: Report CAGR, Sharpe, and max drawdown
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time

from src.analysis.backtesting import create_backtesting_engine, BacktestResult
from src.analysis.ranking_engine import create_ranking_engine


def render_backtesting_interface():
    """
    Render the backtesting interface in Streamlit
    """
    st.title("🔬 Strategy Backtesting")
    st.markdown("Test your investment strategies on historical data to evaluate performance.")
    
    # Sidebar for backtest configuration
    st.sidebar.header("Backtest Configuration")
    
    # Strategy parameters
    st.sidebar.subheader("Strategy Parameters")
    
    # Asset selection
    default_tickers = "AAPL,MSFT,GOOGL,AMZN,TSLA,JPM,V,JNJ,PG,UNH"
    tickers_input = st.sidebar.text_area(
        "Asset Universe (comma-separated)", 
        value=default_tickers,
        help="Enter the tickers you want to include in your backtesting universe"
    )
    tickers = [ticker.strip().upper() for ticker in tickers_input.split(',') if ticker.strip()]
    
    # Date range
    st.sidebar.subheader("Backtest Period")
    default_start = datetime(2022, 1, 1)
    default_end = datetime(2023, 12, 31)
    
    start_date = st.sidebar.date_input(
        "Start Date", 
        value=default_start,
        min_value=datetime(2020, 1, 1),
        max_value=datetime.now() - timedelta(days=30)
    )
    
    end_date = st.sidebar.date_input(
        "End Date", 
        value=default_end,
        min_value=start_date + timedelta(days=30),
        max_value=datetime.now()
    )
    
    # Strategy configuration
    st.sidebar.subheader("Strategy Settings")
    
    initial_capital = st.sidebar.number_input(
        "Initial Capital ($)", 
        min_value=1000, 
        max_value=10000000, 
        value=100000, 
        step=10000
    )
    
    top_n_picks = st.sidebar.slider(
        "Number of Holdings", 
        min_value=1, 
        max_value=min(20, len(tickers)), 
        value=5,
        help="Number of top-ranked stocks to hold"
    )
    
    rebalance_frequency = st.sidebar.selectbox(
        "Rebalancing Frequency",
        options=['monthly', 'weekly', 'daily'],
        index=0,
        help="How often to rebalance the portfolio"
    )
    
    max_position_size = st.sidebar.slider(
        "Max Position Size (%)", 
        min_value=5, 
        max_value=50, 
        value=20,
        help="Maximum percentage of portfolio in any single position"
    ) / 100
    
    # Algorithm weights
    st.sidebar.subheader("Algorithm Weights")
    price_weight = st.sidebar.slider(
        "Price Momentum Weight", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.6, 
        step=0.1
    )
    sentiment_weight = 1.0 - price_weight
    st.sidebar.write(f"Sentiment Weight: {sentiment_weight:.1f}")
    
    # Transaction costs
    transaction_cost = st.sidebar.slider(
        "Transaction Cost (%)", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.1, 
        step=0.05,
        help="Transaction cost as percentage of trade value"
    ) / 100
    
    # Run backtest button
    if st.sidebar.button("🚀 Run Backtest", type="primary"):
        run_backtest_analysis(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            top_n_picks=top_n_picks,
            rebalance_frequency=rebalance_frequency,
            max_position_size=max_position_size,
            price_weight=price_weight,
            sentiment_weight=sentiment_weight,
            transaction_cost=transaction_cost
        )
    
    # Display example/demo if no backtest has been run
    if 'backtest_result' not in st.session_state:
        show_backtesting_help()


def run_backtest_analysis(tickers, start_date, end_date, initial_capital, 
                         top_n_picks, rebalance_frequency, max_position_size,
                         price_weight, sentiment_weight, transaction_cost):
    """
    Run the backtest analysis and display results
    """
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Initializing backtesting engine...")
        progress_bar.progress(10)
        
        # Create engines
        ranking_engine = create_ranking_engine(
            price_weight=price_weight,
            sentiment_weight=sentiment_weight
        )
        
        backtest_engine = create_backtesting_engine(
            ranking_engine=ranking_engine,
            initial_capital=initial_capital,
            rebalance_frequency=rebalance_frequency,
            top_n_picks=top_n_picks,
            transaction_cost=transaction_cost,
            max_position_size=max_position_size
        )
        
        progress_bar.progress(20)
        status_text.text("Running backtest simulation...")
        
        # Run backtest
        result = backtest_engine.run_backtest(tickers, start_date, end_date)
        
        progress_bar.progress(90)
        status_text.text("Generating visualizations...")
        
        # Store result in session state
        st.session_state.backtest_result = result
        st.session_state.backtest_config = {
            'tickers': tickers,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'top_n_picks': top_n_picks,
            'rebalance_frequency': rebalance_frequency,
            'max_position_size': max_position_size,
            'price_weight': price_weight,
            'sentiment_weight': sentiment_weight,
            'transaction_cost': transaction_cost
        }
        
        progress_bar.progress(100)
        status_text.text("Backtest completed!")
        
        # Display results
        display_backtest_results(result)
        
    except Exception as e:
        st.error(f"Backtest failed: {str(e)}")
        st.write("This might be due to network connectivity or data availability issues.")
        st.write("Please try with a different date range or fewer tickers.")
    finally:
        progress_bar.empty()
        status_text.empty()


def display_backtest_results(result: BacktestResult):
    """
    Display comprehensive backtest results
    """
    st.success("🎉 Backtest completed successfully!")
    
    # Performance Summary
    st.header("📊 Performance Summary")
    
    summary = result.summary()
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Return",
            value=summary['Total Return'],
            delta=f"vs. initial: ${result.final_value - result.initial_capital:,.0f}"
        )
    
    with col2:
        st.metric(
            label="CAGR",
            value=summary['CAGR'],
            help="Compound Annual Growth Rate"
        )
    
    with col3:
        st.metric(
            label="Sharpe Ratio",
            value=summary['Sharpe Ratio'],
            help="Risk-adjusted return (higher is better)"
        )
    
    with col4:
        st.metric(
            label="Max Drawdown",
            value=summary['Max Drawdown'],
            delta_color="inverse",
            help="Largest peak-to-trough decline"
        )
    
    # Detailed metrics table
    st.subheader("Detailed Metrics")
    metrics_df = pd.DataFrame(list(summary.items()), columns=['Metric', 'Value'])
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    
    # Portfolio value chart
    if result.portfolio_values and result.portfolio_dates:
        st.header("📈 Portfolio Performance")
        
        # Create portfolio performance chart
        portfolio_df = pd.DataFrame({
            'Date': result.portfolio_dates,
            'Portfolio Value': result.portfolio_values
        })
        
        # Calculate returns for comparison
        portfolio_df['Returns'] = portfolio_df['Portfolio Value'].pct_change()
        portfolio_df['Cumulative Return'] = (portfolio_df['Portfolio Value'] / result.initial_capital - 1) * 100
        
        fig = go.Figure()
        
        # Portfolio value line
        fig.add_trace(go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['Portfolio Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=3),
            hovertemplate='<b>%{x}</b><br>Value: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add initial capital line
        fig.add_hline(
            y=result.initial_capital, 
            line_dash="dash", 
            line_color="gray",
            annotation_text="Initial Capital"
        )
        
        fig.update_layout(
            title='Portfolio Value Over Time',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Returns distribution
        if len(result.daily_returns) > 1:
            st.subheader("📊 Returns Distribution")
            
            returns_df = pd.DataFrame({'Daily Returns': result.daily_returns})
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Returns histogram
                fig_hist = px.histogram(
                    returns_df, 
                    x='Daily Returns',
                    nbins=30,
                    title='Daily Returns Distribution'
                )
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Returns statistics
                returns_stats = {
                    'Mean Daily Return': f"{np.mean(result.daily_returns):.4f}",
                    'Std Daily Return': f"{np.std(result.daily_returns):.4f}",
                    'Best Day': f"{np.max(result.daily_returns):.4f}",
                    'Worst Day': f"{np.min(result.daily_returns):.4f}",
                    'Positive Days': f"{sum(1 for r in result.daily_returns if r > 0)}",
                    'Negative Days': f"{sum(1 for r in result.daily_returns if r < 0)}"
                }
                
                st.write("**Returns Statistics:**")
                for stat, value in returns_stats.items():
                    st.write(f"- {stat}: {value}")
    
    # Trade history
    if result.trade_history:
        st.header("💰 Trade History")
        
        trades_df = pd.DataFrame(result.trade_history)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trades", len(trades_df))
        with col2:
            total_costs = trades_df['transaction_cost'].sum()
            st.metric("Total Trading Costs", f"${total_costs:.2f}")
        with col3:
            avg_trade_size = trades_df['value'].mean()
            st.metric("Avg Trade Size", f"${avg_trade_size:.2f}")
        
        # Show recent trades
        st.subheader("Recent Trades")
        display_trades = trades_df.tail(20).copy()
        
        # Format for display
        display_trades['date'] = pd.to_datetime(display_trades['date']).dt.strftime('%Y-%m-%d')
        display_trades['value'] = display_trades['value'].apply(lambda x: f"${x:,.2f}")
        display_trades['price'] = display_trades['price'].apply(lambda x: f"${x:.2f}")
        display_trades['shares'] = display_trades['shares'].apply(lambda x: f"{x:.2f}")
        display_trades['transaction_cost'] = display_trades['transaction_cost'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            display_trades[['date', 'ticker', 'type', 'shares', 'price', 'value', 'transaction_cost']],
            use_container_width=True,
            hide_index=True
        )
    
    # Download results
    st.header("💾 Download Results")
    
    # Prepare downloadable data
    if st.button("📥 Download Detailed Results"):
        create_downloadable_results(result)


def create_downloadable_results(result: BacktestResult):
    """
    Create downloadable CSV files with backtest results
    """
    
    # Portfolio performance data
    if result.portfolio_values and result.portfolio_dates:
        portfolio_df = pd.DataFrame({
            'Date': result.portfolio_dates,
            'Portfolio_Value': result.portfolio_values
        })
        
        csv_portfolio = portfolio_df.to_csv(index=False)
        st.download_button(
            label="Download Portfolio Performance",
            data=csv_portfolio,
            file_name=f"backtest_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Trade history
    if result.trade_history:
        trades_df = pd.DataFrame(result.trade_history)
        csv_trades = trades_df.to_csv(index=False)
        st.download_button(
            label="Download Trade History",
            data=csv_trades,
            file_name=f"backtest_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def show_backtesting_help():
    """
    Show help and examples for backtesting
    """
    st.header("🎯 About Strategy Backtesting")
    
    st.markdown("""
    **Backtesting** allows you to test investment strategies on historical data to evaluate their performance.
    This helps you understand how your strategy would have performed in the past before risking real money.
    
    ### Key Features:
    - **Historical Simulation**: Test strategies on real market data
    - **Performance Metrics**: CAGR, Sharpe ratio, maximum drawdown, and more
    - **Customizable Strategy**: Adjust weights, rebalancing frequency, and holdings
    - **Transaction Costs**: Realistic simulation including trading costs
    - **Risk Management**: Position size limits and diversification
    
    ### How to Use:
    1. **Configure Strategy**: Set your asset universe and strategy parameters
    2. **Choose Period**: Select the historical period to test
    3. **Run Backtest**: Click "Run Backtest" to simulate the strategy
    4. **Analyze Results**: Review performance metrics and visualizations
    5. **Download Data**: Export results for further analysis
    
    ### Key Metrics Explained:
    - **CAGR**: Compound Annual Growth Rate - the annual return rate
    - **Sharpe Ratio**: Risk-adjusted return (higher is better)
    - **Max Drawdown**: Largest peak-to-trough decline (lower is better)
    - **Win Rate**: Percentage of profitable trades
    
    ### ⚠️ Important Notes:
    - Past performance does not guarantee future results
    - Backtests assume perfect execution and may not reflect real trading conditions
    - Always start with paper trading before using real money
    - Consider market conditions and regime changes
    """)
    
    # Example configuration
    st.subheader("📋 Example Configuration")
    
    example_config = {
        "Asset Universe": "AAPL, MSFT, GOOGL, AMZN, TSLA",
        "Period": "2022-01-01 to 2023-12-31",
        "Initial Capital": "$100,000",
        "Holdings": "Top 5 ranked stocks",
        "Rebalancing": "Monthly",
        "Price Weight": "60%",
        "Sentiment Weight": "40%",
        "Max Position": "20%"
    }
    
    for key, value in example_config.items():
        st.write(f"**{key}**: {value}")
    
    st.info("👆 Configure your backtest parameters in the sidebar and click 'Run Backtest' to get started!")


# Additional utility functions for backtesting dashboard
def compare_strategies():
    """
    Future enhancement: Compare multiple strategies side by side
    """
    pass


def benchmark_comparison():
    """
    Future enhancement: Compare strategy performance against benchmarks (S&P 500, etc.)
    """
    pass


if __name__ == "__main__":
    # For testing the backtesting dashboard independently
    st.set_page_config(
        page_title="Strategy Backtesting",
        page_icon="🔬",
        layout="wide"
    )
    
    render_backtesting_interface()