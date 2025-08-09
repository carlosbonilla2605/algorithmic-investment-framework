"""
Main Streamlit Dashboard for the Algorithmic Investment Framework

This dashboard provides an interactive interface for analyzing stocks and ETFs
using the ranking algorithm that combines price momentum and news sentiment.
"""

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

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.analysis.ranking_engine import create_ranking_engine
from src.data_acquisition.market_data import create_market_data_manager

# Page configuration
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


@st.cache_data(ttl=300)  # Cache for 5 minutes
def run_ranking_analysis(tickers, price_weight, sentiment_weight):
    """Cached function to run ranking analysis"""
    engine = create_ranking_engine(price_weight, sentiment_weight)
    return engine.rank_assets(tickers, include_details=True)


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
    if st.sidebar.button("🚀 Run Analysis", type="primary"):
        st.rerun()
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5 min)", value=False)
    if auto_refresh:
        time.sleep(1)  # Small delay to prevent too frequent refreshes
        st.rerun()
    
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
            rankings_df = run_ranking_analysis(tickers, price_weight, sentiment_weight)
            
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
    
    # Top picks section
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
        
        # Score breakdown
        st.subheader(f"Score Breakdown for {selected_ticker}")

        # Expandable table for headlines and sentiment
        st.markdown("---")
        with st.expander(f"📰 News Headlines & Sentiment for {selected_ticker}"):
            news_manager = create_news_sentiment_manager()
            sentiment_analyzer = SentimentAnalyzer()
            news_data = news_manager.get_sentiment_for_ticker(selected_ticker)
            headlines = news_data.get('headlines', [])
            if headlines:
                headline_sentiments = [sentiment_analyzer.analyze_sentiment(h) for h in headlines]
                table_data = [
                    {
                        'Headline': h,
                        'Sentiment': s['compound'],
                        'Positive': s['positive'],
                        'Neutral': s['neutral'],
                        'Negative': s['negative']
                    }
                    for h, s in zip(headlines, headline_sentiments)
                ]
                st.dataframe(table_data, use_container_width=True)
            else:
                st.info("No headlines available for this asset.")
        
        score_data = {
            'Component': ['Technical Score', 'Sentiment Score', 'Composite Score'],
            'Score': [asset_data['technical_score'], asset_data['sentiment_score'], asset_data['composite_score']],
            'Weight': ['60%', '40%', '100%']
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_gauge = go.Figure()
            
            fig_gauge.add_trace(go.Bar(
                x=['Technical', 'Sentiment', 'Composite'],
                y=[asset_data['technical_score'], asset_data['sentiment_score'], asset_data['composite_score']],
                marker_color=['lightblue', 'lightcoral', 'lightgreen'],
                text=[f"{asset_data['technical_score']:.1f}", 
                      f"{asset_data['sentiment_score']:.1f}", 
                      f"{asset_data['composite_score']:.1f}"],
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
            st.write(f"**Headlines Analyzed:** {asset_data['headline_count']}")
            st.write(f"**Positive News:** {asset_data['positive_ratio']:.1%}")
            st.write(f"**Volume:** {asset_data['volume']:,.0f}")
            
            if asset_data['sentiment_std'] > 0:
                st.write(f"**Sentiment Consistency:** {(1-asset_data['sentiment_std']):.1%}")
        
        # Historical chart
        st.subheader(f"📈 Price History for {selected_ticker}")
        
        with col4:
            st.metric("Composite Score", f"{asset_data['composite_score']:.1f}/100")

    # Expandable table for headlines and sentiment
    st.markdown("---")
    with st.expander(f"📰 News Headlines & Sentiment for {selected_ticker}"):
        news_manager = create_news_sentiment_manager()
        sentiment_analyzer = SentimentAnalyzer()
        news_data = news_manager.get_sentiment_for_ticker(selected_ticker)
        headlines = news_data.get('headlines', [])
        if headlines:
            headline_sentiments = [sentiment_analyzer.analyze_sentiment(h) for h in headlines]
            table_data = [
                {
                    'Headline': h,
                    'Sentiment': s['compound'],
                    'Positive': s['positive'],
                    'Neutral': s['neutral'],
                    'Negative': s['negative']
                }
                for h, s in zip(headlines, headline_sentiments)
            ]
            st.dataframe(table_data, use_container_width=True)
        else:
            st.info("No headlines available for this asset.")

if __name__ == "__main__":
    main()
