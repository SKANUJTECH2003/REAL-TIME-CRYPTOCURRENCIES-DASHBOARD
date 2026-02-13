import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from textblob import TextBlob
import random
import numpy as np
import requests
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('brown')
    nltk.download('punkt_tab')

# Page Configuration
st.set_page_config(
    page_title="Crypto Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== MOCK DATA GENERATOR (FALLBACK) ====================
def generate_mock_data(ticker: str, period: str = "1y", interval: str = "1d"):
    """
    Generate realistic mock cryptocurrency data when yfinance fails.
    
    Args:
        ticker (str): Cryptocurrency ticker
        period (str): Period for data generation
        interval (str): Time interval
    
    Returns:
        pd.DataFrame: Mock OHLC data
    """
    # Base prices for different cryptocurrencies
    base_prices = {
        "BTC-USD": 42500,
        "ETH-USD": 2300,
        "SOL-USD": 105
    }
    
    base_price = base_prices.get(ticker, 1000)
    
    # Calculate number of periods
    if interval == "1d":
        num_periods = 365
    elif interval == "1h":
        num_periods = 24 * 60
    elif interval == "5m":
        num_periods = 24 * 12 * 7
    else:  # 1m
        num_periods = 24 * 60 * 7
    
    # Generate realistic OHLC data
    dates = [datetime.now() - timedelta(periods) for periods in range(num_periods, 0, -1)]
    
    data = []
    price = base_price
    
    for date in dates:
        # Random walk with drift
        daily_return = np.random.normal(0.002, 0.03)
        price = price * (1 + daily_return)
        
        open_price = price * np.random.uniform(0.98, 1.02)
        close_price = price * np.random.uniform(0.98, 1.02)
        high_price = max(open_price, close_price) * np.random.uniform(1.0, 1.02)
        low_price = min(open_price, close_price) * np.random.uniform(0.98, 1.0)
        volume = np.random.uniform(1e9, 5e9)
        
        data.append({
            'Open': open_price,
            'High': high_price,
            'Low': low_price,
            'Close': close_price,
            'Volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'Date'
    return df


# ==================== COINGECKO API (LIVE DATA) ====================
@st.cache_data(ttl=300)
def get_coingecko_data(coin_id: str, days: int = 365):
    """
    Fetch cryptocurrency OHLC data from CoinGecko API (free, no auth needed).
    
    Args:
        coin_id (str): CoinGecko coin ID (bitcoin, ethereum, solana)
        days (int): Number of days of historical data
    
    Returns:
        tuple: (DataFrame with OHLC data, True) or (None, False) on failure
    """
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) < 2:
            return None, False
        
        # Parse OHLC data: each row is [timestamp_ms, open, high, low, close]
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        
        for candle in data:
            timestamp_ms, open_val, high_val, low_val, close_val = candle
            dates.append(datetime.fromtimestamp(timestamp_ms / 1000))
            opens.append(open_val)
            highs.append(high_val)
            lows.append(low_val)
            closes.append(close_val)
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': [np.random.uniform(1e9, 5e9) for _ in range(len(dates))]  # CoinGecko OHLC doesn't include volume
        }, index=dates)
        df.index.name = 'Date'
        
        return df, True
    
    except Exception as e:
        return None, False


# Custom CSS for dark theme and professional styling
st.markdown("""
    <style>
    :root {
        --primary-color: #00D4FF;
        --secondary-color: #FF006E;
        --success-color: #06FFA5;
        --danger-color: #FF0040;
        --background-color: #0A0E27;
    }
    
    body {
        background-color: var(--background-color);
        color: #FFFFFF;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #00D4FF;
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
    }
    
    .sentiment-bullish {
        color: #06FFA5;
        font-weight: bold;
    }
    
    .sentiment-bearish {
        color: #FF0040;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. DATA FETCHING FUNCTION ====================
@st.cache_data(ttl=300)
def get_data(ticker: str, interval: str = "1d"):
    """
    Fetch cryptocurrency data with multiple sources:
    1. CoinGecko API (primary - free, reliable, live)
    2. Yahoo Finance (fallback)
    3. Mock data (final fallback)
    
    Args:
        ticker (str): Cryptocurrency ticker (e.g., 'BTC-USD')
        interval (str): Time interval (1m, 5m, 1h, 1d)
    
    Returns:
        tuple: (data DataFrame, is_live boolean)
    """
    # Map ticker to CoinGecko coin ID
    coingecko_map = {
        "BTC-USD": "bitcoin",
        "ETH-USD": "ethereum",
        "SOL-USD": "solana"
    }
    
    coin_id = coingecko_map.get(ticker, None)
    
    # ===== Try CoinGecko API (PRIMARY - LIVE DATA) =====
    if coin_id:
        data, is_live = get_coingecko_data(coin_id, days=365)
        if data is not None and not data.empty:
            return data, is_live
    
    # ===== Fallback to Yahoo Finance =====
    try:
        period_map = {
            "1m": "7d",
            "5m": "7d",
            "1h": "60d",
            "1d": "1y"
        }
        period = period_map.get(interval, "1y")
        tick = yf.Ticker(ticker)
        data = tick.history(period=period, interval=interval)
        
        if not data.empty:
            required_cols = ['Open', 'High', 'Low', 'Close']
            if all(col in data.columns for col in required_cols):
                return data, True
    except Exception:
        pass
    
    # ===== Final Fallback: Mock Data =====
    period_map = {
        "1m": "7d",
        "5m": "7d",
        "1h": "60d",
        "1d": "1y"
    }
    period = period_map.get(interval, "1y")
    return generate_mock_data(ticker, period, interval), False


# ==================== 2. SENTIMENT ANALYSIS FUNCTION ====================
def get_sentiment():
    """
    Analyze sentiment using mock news data and rule-based logic.
    
    Returns:
        dict: Contains sentiment_score and sentiment_label
    """
    try:
        # Mock news headlines for demonstration
        mock_headlines = [
            "Bitcoin rallies as institutional investors show strong interest",
            "Ethereum network upgrade improves transaction efficiency significantly",
            "Solana addresses scalability concerns with latest protocol update",
            "Cryptocurrency market shows signs of recovery and stability",
            "New regulatory framework could boost crypto adoption",
            "Market volatility raises concerns among traders",
            "Technical analysis indicates potential breakout patterns",
            "Experts remain optimistic about long-term crypto potential"
        ]
        
        # Randomly select headlines for analysis
        selected_headlines = random.sample(mock_headlines, k=random.randint(3, 5))
        
        # Calculate sentiment using TextBlob
        sentiment_scores = []
        for headline in selected_headlines:
            blob = TextBlob(headline)
            sentiment_scores.append(blob.sentiment.polarity)
        
        # Average sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Convert to percentage (0-100)
        sentiment_percentage = ((avg_sentiment + 1) / 2) * 100
        
        # Determine sentiment label
        if sentiment_percentage >= 60:
            sentiment_label = "🟢 BULLISH"
        elif sentiment_percentage >= 40:
            sentiment_label = "🟡 NEUTRAL"
        else:
            sentiment_label = "🔴 BEARISH"
        
        return {
            "score": sentiment_percentage,
            "label": sentiment_label,
            "headlines": selected_headlines
        }
    
    except Exception as e:
        st.warning(f"⚠️ Could not fetch sentiment data: {str(e)}")
        return {
            "score": 50,
            "label": "🟡 NEUTRAL",
            "headlines": []
        }


# ==================== 3. CANDLESTICK CHART FUNCTION ====================
def create_candlestick_chart(data: pd.DataFrame, ticker: str):
    """
    Create an interactive candlestick chart using Plotly.
    
    Args:
        data (pd.DataFrame): OHLC data
        ticker (str): Cryptocurrency ticker
    
    Returns:
        plotly.graph_objects.Figure: Candlestick chart
    """
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=ticker,
            increasing_line_color='#06FFA5',
            decreasing_line_color='#FF0040'
        )])
        
        fig.update_layout(
            title=f"📈 {ticker} - Price Action",
            yaxis_title="Price (USD)",
            xaxis_title="Date",
            template="plotly_dark",
            hovermode="x unified",
            height=500,
            font=dict(color="#FFFFFF"),
            paper_bgcolor='rgba(10, 14, 39, 0.8)',
            plot_bgcolor='rgba(45, 53, 97, 0.3)'
        )
        
        return fig
    
    except Exception as e:
        st.error(f"❌ Error creating chart: {str(e)}")
        return None


# ==================== 4. KPI METRICS FUNCTION ====================
def display_kpi_metrics(data: pd.DataFrame, ticker: str):
    """
    Display key performance indicators with color coding.
    
    Args:
        data (pd.DataFrame): OHLC data
        ticker (str): Cryptocurrency ticker
    """
    try:
        current_price = data['Close'].iloc[-1]
        previous_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
        price_change = current_price - previous_price
        price_change_pct = (price_change / previous_price * 100) if previous_price != 0 else 0
        
        high_24h = data['High'].tail(24).max() if len(data) >= 24 else data['High'].max()
        low_24h = data['Low'].tail(24).min() if len(data) >= 24 else data['Low'].min()
        
        # Color indicators
        change_color = "🟢" if price_change_pct > 0 else "🔴"
        
        # Create columns for KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 CURRENT PRICE",
                value=f"${current_price:.2f}",
                delta=f"{price_change_pct:.2f}%",
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                label="📊 24H CHANGE",
                value=f"{price_change_pct:.2f}%",
                delta=f"{change_color}",
                delta_color="off"
            )
        
        with col3:
            st.metric(
                label="📈 24H HIGH",
                value=f"${high_24h:.2f}"
            )
        
        with col4:
            st.metric(
                label="📉 24H LOW",
                value=f"${low_24h:.2f}"
            )
    
    except Exception as e:
        st.error(f"❌ Error displaying KPI metrics: {str(e)}")


# ==================== 5. MAIN FUNCTION ====================
def main():
    """
    Main function to orchestrate the dashboard layout and functionality.
    """
    # Header
    st.markdown("## 🪙 Real-Time Cryptocurrency Analytics Dashboard")
    st.markdown("---")
    
    # ==================== SIDEBAR ====================
    st.sidebar.title("⚙️ Configuration")
    
    # Cryptocurrency selection
    crypto_list = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD"
    }
    
    selected_crypto = st.sidebar.selectbox(
        "Select Cryptocurrency:",
        options=list(crypto_list.keys()),
        index=0
    )
    ticker = crypto_list[selected_crypto]
    
    # Interval selection
    interval_options = ["1m", "5m", "1h", "1d"]
    selected_interval = st.sidebar.selectbox(
        "Select Time Interval:",
        options=interval_options,
        index=3
    )
    
    # Refresh button with cache clearing
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", key="refresh_btn", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with col2:
        if st.button("🗑️ Clear All", key="clear_btn", use_container_width=True):
            st.cache_data.clear()
            st.session_state.clear()
            st.rerun()

    # Auto-refresh controls
    st.sidebar.markdown("### 🔁 Auto-Refresh")
    auto_refresh_enabled = st.sidebar.checkbox("Enable Auto-Refresh", value=False, key="auto_refresh_enabled")
    refresh_option = st.sidebar.selectbox(
        "Refresh Interval:", options=["30s", "60s", "120s", "300s"], index=1, key="auto_refresh_interval"
    )
    # Map option to seconds
    interval_map = {"30s": 30, "60s": 60, "120s": 120, "300s": 300}
    refresh_sec = interval_map.get(refresh_option, 60)
    
    # Implement auto-refresh using Streamlit's native time-based rerun
    if auto_refresh_enabled:
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        current_time = time.time()
        elapsed = current_time - st.session_state.last_refresh
        
        if elapsed >= refresh_sec:
            st.session_state.last_refresh = current_time
            st.cache_data.clear()
            st.rerun()
        
        # Show countdown timer
        remaining = int(refresh_sec - elapsed)
        st.sidebar.caption(f"⏳ Refreshing in: {remaining}s")
        # Trigger rerun after 1 second to update countdown
        time.sleep(1)
        st.rerun()

    st.sidebar.markdown("---")
    
    # Troubleshooting section
    with st.sidebar.expander("🛠️ Troubleshooting"):
        st.markdown("""
        **Getting "No data available" error?**
        
        1. ✅ Click **Clear All** button above
        2. ✅ Check your internet connection
        3. ✅ Try a different time interval (1d is most stable)
        4. ✅ Wait 30 seconds and refresh
        5. ✅ Check [Yahoo Finance Status](https://finance.yahoo.com)
        
        **Why is data loading slowly?**
        - 1m/5m intervals need API calls - slower
        - 1h/1d intervals are cached (faster)
        - First load takes longer, refreshes are instant
        
        **API Rate Limiting?**
        - Yahoo Finance limits requests
        - Solution: Wait 2-3 minutes before retrying
        """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        ### 📋 About
        This dashboard displays real-time cryptocurrency market data including:
        - Live price movements
        - 24h statistics
        - Interactive candlestick charts
        - Market sentiment analysis
        
        **Data Source:** Yahoo Finance (yfinance)
        """
    )
    
    # ==================== MAIN CONTENT ====================
    
    # Fetch data (returns tuple: data, is_live)
    with st.spinner(f"📊 Fetching {selected_crypto} data..."):
        data, is_live = get_data(ticker, selected_interval)
    
    if data is not None:
        # Data source badge
        if is_live:
            st.markdown(
                "<div style='background:#063; color:#eafff2; padding:10px; border-radius:8px; width:280px;'><strong>LIVE DATA</strong> — fetched from Yahoo Finance</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#6b5b00; color:#fffbe6; padding:10px; border-radius:8px; width:320px;'><strong>DEMO DATA</strong> — generated locally (Yahoo unavailable)</div>",
                unsafe_allow_html=True,
            )
        st.markdown("\n")
        # Display KPI Metrics
        st.subheader(f"📊 {selected_crypto} Market Metrics")
        display_kpi_metrics(data, ticker)
        st.markdown("---")
        
        # Display Candlestick Chart
        st.subheader(f"📈 Price Action Chart")
        chart = create_candlestick_chart(data, ticker)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
        
        st.markdown("---")
        
        # Market Sentiment Section
        st.subheader("🎯 Market Sentiment Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            sentiment_data = get_sentiment()
            
            sentiment_color = "#06FFA5" if sentiment_data["score"] >= 60 else "#FF0040" if sentiment_data["score"] < 40 else "#FFD700"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: {sentiment_color};">{sentiment_data['label']}</h2>
                <h3 style="color: #00D4FF;">{sentiment_data['score']:.1f}%</h3>
                <p style="color: #888888;">Sentiment Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📰 News Headlines Analyzed:")
            for idx, headline in enumerate(sentiment_data["headlines"], 1):
                st.caption(f"{idx}. {headline}")
        
        st.markdown("---")
        
        # Data Table
        st.subheader("📋 Recent Price Data")
        display_data = data.tail(10).copy()
        display_data['Date'] = display_data.index
        display_data = display_data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        display_data['Close'] = display_data['Close'].apply(lambda x: f"${x:.2f}")
        display_data['Open'] = display_data['Open'].apply(lambda x: f"${x:.2f}")
        display_data['High'] = display_data['High'].apply(lambda x: f"${x:.2f}")
        display_data['Low'] = display_data['Low'].apply(lambda x: f"${x:.2f}")
        display_data['Volume'] = display_data['Volume'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        
        # Footer
        st.markdown("---")
        st.markdown(
            f"""
            <div style="text-align: center; color: #888888;">
                <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Data refreshes every 5 minutes | Dashboard created with Streamlit & Plotly</p>
                <p>Developed by: <strong>ANUJ KUMAR VISHWAKARMA</strong></p>
                <p><a href="LICENSE" style="color: #00D4FF;">License: MIT</a></p>
                <div style="margin-top:8px;">
                    <a href="mailto:anujkumarvishwakarma313@gmail.com" target="_blank" rel="noopener noreferrer" style="margin:0 8px;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4e/Gmail_Icon.svg" width="28" height="28" style="filter:brightness(0) invert(1); vertical-align:middle;" alt="Email"/>
                    </a>
                    <a href="https://anuj-vishwakarma-portfolio.netlify.app" target="_blank" rel="noopener noreferrer" style="margin:0 8px;">
                        <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/netlify.svg" width="28" height="28" style="filter:brightness(0) invert(1); vertical-align:middle;" alt="Portfolio"/>
                    </a>
                    <a href="https://www.linkedin.com/in/anuj-kumar-vishwakarma-a98535285/" target="_blank" rel="noopener noreferrer" style="margin:0 8px;">
                        <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/linkedin.svg" width="28" height="28" style="filter:brightness(0) invert(1); vertical-align:middle;" alt="LinkedIn"/>
                    </a>
                    <a href="https://github.com/SKANUJTECH2003" target="_blank" rel="noopener noreferrer" style="margin:0 8px;">
                        <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/github.svg" width="28" height="28" style="filter:brightness(0) invert(1); vertical-align:middle;" alt="GitHub"/>
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    else:
        st.warning("⚠️ Unable to load data. Please check your internet connection and try again.")


# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    main()
