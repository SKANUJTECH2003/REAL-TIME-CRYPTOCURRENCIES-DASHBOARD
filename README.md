# 🪙 Real-Time Cryptocurrency Analytics Dashboard

A professional-grade Streamlit application for real-time cryptocurrency market analysis with interactive charts and sentiment analysis.

## 🌟 Features

### 📊 Real-Time Market Data
- Live price fetching for Bitcoin (BTC), Ethereum (ETH), and Solana (SOL)
- Multiple time intervals: 1m, 5m, 1h, 1d
- Cached data (5-minute TTL) for optimal performance
- Comprehensive error handling for network and API issues

### 📈 Interactive Visualizations
- Candlestick charts powered by Plotly
- Real-time KPI metrics with color-coded indicators
- 24-hour high/low price tracking
- Price change percentage with visual indicators

### 🎯 Market Sentiment Analysis
- Mock news headline analysis using TextBlob
- Bullish/Bearish/Neutral sentiment classification
- Sentiment score visualization (0-100%)
- Sample headlines with sentiment context

### 🎨 Professional Design
- Dark theme with gradient styling
- Responsive layout with optimized spacing
- Mobile-friendly interface
- LinkedIn-ready appearance

### 🛡️ Robust Error Handling
- Try-except blocks for all data fetching operations
- User-friendly error messages
- Loading spinners for better UX
- Graceful degradation on API failures

## 📋 Requirements

```
streamlit==1.28.1
yfinance==0.2.32
pandas==2.1.3
plotly==5.18.0
textblob==0.17.1
```

## 🚀 Installation & Setup

### 1. Clone or download the project
```bash
cd "c:\Users\Anjali Vishawakarma\OneDrive\Desktop\NEW PROJECT"
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download TextBlob corpora (required for sentiment analysis)
```bash
python -m textblob.download_corpora
```

### 5. Run the application
```bash
streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

## 📖 Usage Guide

### Sidebar Controls
- **Select Cryptocurrency**: Choose between Bitcoin, Ethereum, or Solana
- **Select Time Interval**: Pick your preferred time frame (1m, 5m, 1h, 1d)
- **Refresh Data**: Manually clear cache and fetch fresh data

### Dashboard Sections

#### 1. Market Metrics (Top)
- **Current Price**: Latest cryptocurrency price
- **24H Change**: Percentage change in the last 24 hours
- **24H High**: Highest price in the last 24 hours
- **24H Low**: Lowest price in the last 24 hours

#### 2. Price Action Chart
- Interactive candlestick chart
- Green candles = price increased
- Red candles = price decreased
- Hover for detailed OHLC data

#### 3. Market Sentiment
- Sentiment score (0-100%)
- Bullish/Bearish/Neutral classification
- Recent news headlines analyzed

#### 4. Data Table
- Last 10 price updates
- Open, High, Low, Close prices
- Trading volume

## 🏗️ Code Structure

### Main Functions

#### `get_data(ticker, interval)`
- Fetches cryptocurrency data from Yahoo Finance
- Implements caching with 5-minute TTL
- Handles errors gracefully
- Parameters:
  - `ticker`: Cryptocurrency ticker (e.g., 'BTC-USD')
  - `interval`: Time interval ('1m', '5m', '1h', '1d')
- Returns: DataFrame with OHLC data or None

#### `get_sentiment()`
- Analyzes mock news headlines
- Calculates sentiment using TextBlob
- Returns sentiment score and classification
- Returns: Dict with score, label, and headlines

#### `create_candlestick_chart(data, ticker)`
- Generates interactive Plotly candlestick chart
- Customized with professional dark theme
- Parameters:
  - `data`: DataFrame with OHLC data
  - `ticker`: Cryptocurrency ticker
- Returns: Plotly Figure object

#### `display_kpi_metrics(data, ticker)`
- Displays four key metrics using Streamlit
- Color-coded indicators for price changes
- Parameters:
  - `data`: DataFrame with OHLC data
  - `ticker`: Cryptocurrency ticker

#### `main()`
- Orchestrates dashboard layout
- Manages sidebar configuration
- Combines all components

## 🎯 Performance Optimization

1. **Data Caching**: Uses `@st.cache_data` decorator with 5-minute TTL
2. **Lazy Loading**: Charts only render when necessary
3. **Efficient Filtering**: Tail operations instead of full data processing
4. **Streaming Updates**: Real-time data without page reloads

## 🔧 Customization

### Change Theme Colors
Edit the CSS section in `app.py`:
```python
--primary-color: #00D4FF;
--secondary-color: #FF006E;
--success-color: #06FFA5;
--danger-color: #FF0040;
```

### Add More Cryptocurrencies
Modify the `crypto_list` in the `main()` function:
```python
crypto_list = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Solana": "SOL-USD",
    "Cardano": "ADA-USD",  # Add here
}
```

### Adjust Cache Duration
Change the TTL value in the `@st.cache_data` decorator (in seconds):
```python
@st.cache_data(ttl=600)  # 10 minutes instead of 5
```

## 📊 Data Source

- **Primary Source**: Yahoo Finance (yfinance library)
- **Sentiment**: Mock headlines with TextBlob analysis
- **Update Frequency**: Real-time with caching

## ⚠️ Error Handling

The application handles:
- No internet connection
- API rate limits
- Invalid ticker symbols
- Empty data responses
- Chart rendering errors

All errors are displayed with helpful user tips.

## 🐛 Troubleshooting

### "No data available for ticker"
- Check your internet connection
- Verify the cryptocurrency is still trading
- Try a different time interval

### "ModuleNotFoundError"
- Ensure all packages are installed: `pip install -r requirements.txt`
- Verify you're in the correct virtual environment

### Slow Performance
- Try a larger time interval (1d instead of 1m)
- Clear cache manually using the refresh button
- Close other memory-intensive applications

## 📈 LinkedIn Showcase Ready

This dashboard features:
- Professional dark UI/UX
- Real-time data integration
- Advanced data visualization
- Sentiment analysis capabilities
- Production-grade error handling
- Performance optimization techniques

Perfect for data engineering portfolios!

## 📝 License

Open source - Feel free to modify and distribute

## 🤝 Support

For issues or feature requests, refer to:
- Streamlit Documentation: https://docs.streamlit.io
- yfinance Documentation: https://yfinance.readthedocs.io
- Plotly Documentation: https://plotly.com/python

---

**Happy analyzing! 🚀**
