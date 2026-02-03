import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# Page configuration
st.set_page_config(
    page_title="Stock Watchlist App",
    page_icon="📈",
    layout="wide"
)

# Initialize session state for watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Load watchlist from file if exists
WATCHLIST_FILE = 'watchlist.json'


def load_watchlist():
    """Load watchlist from JSON file"""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_watchlist():
    """Save watchlist to JSON file"""
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(st.session_state.watchlist, f)


# Load watchlist on app start
if not st.session_state.watchlist:
    st.session_state.watchlist = load_watchlist()


def get_stock_data(ticker, period="3y", interval=None):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)

        # Use appropriate interval for different periods
        if interval is None:
            if period == "1d":
                interval = "5m"  # 5-minute intervals for 1 day
            elif period in ["5d", "1wk"]:
                interval = "15m"  # 15-minute intervals for 1 week
            else:
                interval = "1d"  # Daily intervals for longer periods

        data = stock.history(period=period, interval=interval)
        if data.empty:
            return None, None
        info = stock.info
        return data, info
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None, None


def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index (RSI)"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_moving_average(data, period=200):
    """Calculate Simple Moving Average"""
    return data['Close'].rolling(window=period).mean()


def create_stock_chart(data, ticker, chart_type='candlestick', show_ma=False, ma_period=200):
    """Create interactive chart using Plotly"""
    fig = go.Figure()

    if chart_type == 'line':
        # Line chart for shorter periods
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#1f77b4', width=2),
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))

        # Add moving average if requested and enough data points
        if show_ma and len(data) >= ma_period:
            ma = calculate_moving_average(data, ma_period)
            fig.add_trace(go.Scatter(
                x=data.index,
                y=ma,
                mode='lines',
                name=f'{ma_period}-Period MA',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))

        # Add volume as bar chart
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color='rgba(100, 100, 250, 0.3)')
        ))

        # Update layout for line chart
        fig.update_layout(
            title=f'{ticker} - Price Performance',
            yaxis_title='Close Price (USD)',
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right'
            ),
            xaxis_rangeslider_visible=False,
            height=600,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True
        )
    else:
        # Candlestick chart for longer periods
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ))

        # Add moving average if requested and enough data points
        if show_ma and len(data) >= ma_period:
            ma = calculate_moving_average(data, ma_period)
            fig.add_trace(go.Scatter(
                x=data.index,
                y=ma,
                mode='lines',
                name=f'{ma_period}-Period MA',
                line=dict(color='#ff7f0e', width=2)
            ))

        # Volume bar chart
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color='rgba(100, 100, 250, 0.3)')
        ))

        # Update layout for candlestick
        fig.update_layout(
            title=f'{ticker} - Candlestick Chart',
            yaxis_title='Price (USD)',
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right'
            ),
            xaxis_rangeslider_visible=False,
            height=600,
            hovermode='x unified',
            template='plotly_white'
        )

    return fig


def create_rsi_chart(data, ticker, rsi_period=14):
    """Create RSI indicator chart"""
    rsi = calculate_rsi(data, rsi_period)

    fig = go.Figure()

    # RSI line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=rsi,
        mode='lines',
        name=f'RSI ({rsi_period})',
        line=dict(color='#9467bd', width=2)
    ))

    # Add overbought line (70)
    fig.add_hline(y=70, line_dash="dash", line_color="red",
                  annotation_text="Overbought (70)",
                  annotation_position="right")

    # Add oversold line (30)
    fig.add_hline(y=30, line_dash="dash", line_color="green",
                  annotation_text="Oversold (30)",
                  annotation_position="right")

    # Add middle line (50)
    fig.add_hline(y=50, line_dash="dot", line_color="gray",
                  annotation_text="Neutral (50)",
                  annotation_position="right")

    # Shade overbought and oversold regions
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)

    fig.update_layout(
        title=f'{ticker} - RSI Indicator',
        yaxis_title='RSI',
        xaxis_title='Date',
        height=300,
        hovermode='x unified',
        template='plotly_white',
        yaxis=dict(range=[0, 100])
    )

    return fig, rsi


def add_to_watchlist(ticker):
    """Add stock to watchlist"""
    ticker = ticker.upper().strip()
    if ticker and ticker not in st.session_state.watchlist:
        # Verify ticker exists
        data, info = get_stock_data(ticker, period="5d")
        if data is not None:
            st.session_state.watchlist.append(ticker)
            save_watchlist()
            st.success(f"✅ {ticker} added to watchlist!")
            return True
        else:
            st.error(f"❌ Invalid ticker symbol: {ticker}")
            return False
    elif ticker in st.session_state.watchlist:
        st.warning(f"⚠️ {ticker} is already in your watchlist")
        return False
    return False


def remove_from_watchlist(ticker):
    """Remove stock from watchlist"""
    if ticker in st.session_state.watchlist:
        st.session_state.watchlist.remove(ticker)
        save_watchlist()
        st.success(f"🗑️ {ticker} removed from watchlist")


def display_stock_info(info, ticker):
    """Display stock information in a nice format"""
    if info:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            st.metric("Current Price",
                      f"${current_price:.2f}" if isinstance(current_price, (int, float)) else current_price)

        with col2:
            prev_close = info.get('previousClose', 'N/A')
            if isinstance(current_price, (int, float)) and isinstance(prev_close, (int, float)):
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                st.metric("Change", f"${change:.2f}", f"{change_pct:.2f}%")
            else:
                st.metric("Previous Close",
                          f"${prev_close:.2f}" if isinstance(prev_close, (int, float)) else prev_close)

        with col3:
            market_cap = info.get('marketCap', 'N/A')
            if isinstance(market_cap, (int, float)):
                if market_cap >= 1e12:
                    market_cap_str = f"${market_cap / 1e12:.2f}T"
                elif market_cap >= 1e9:
                    market_cap_str = f"${market_cap / 1e9:.2f}B"
                elif market_cap >= 1e6:
                    market_cap_str = f"${market_cap / 1e6:.2f}M"
                else:
                    market_cap_str = f"${market_cap:,.0f}"
                st.metric("Market Cap", market_cap_str)
            else:
                st.metric("Market Cap", market_cap)

        with col4:
            volume = info.get('volume', info.get('regularMarketVolume', 'N/A'))
            if isinstance(volume, (int, float)):
                volume_str = f"{volume:,.0f}"
                st.metric("Volume", volume_str)
            else:
                st.metric("Volume", volume)

        # Additional info
        st.markdown("---")
        col5, col6, col7 = st.columns(3)

        with col5:
            st.write(f"**Company:** {info.get('longName', ticker)}")
            st.write(f"**Sector:** {info.get('sector', 'N/A')}")

        with col6:
            st.write(f"**52 Week High:** ${info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.write(f"**52 Week Low:** ${info.get('fiftyTwoWeekLow', 'N/A')}")

        with col7:
            st.write(f"**PE Ratio:** {info.get('trailingPE', 'N/A')}")
            st.write(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")


# Main App Layout
st.title("📈 Stock Watchlist App")
st.markdown("Track your favorite stocks with real-time data and 3-year historical charts")

# Sidebar
with st.sidebar:
    st.header("🔍 Add Stock")
    new_ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA)", key="ticker_input")
    if st.button("Add to Watchlist", type="primary"):
        if new_ticker:
            add_to_watchlist(new_ticker)
            st.rerun()

    st.markdown("---")
    st.header("📋 Your Watchlist")

    if st.session_state.watchlist:
        for ticker in st.session_state.watchlist:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📊 {ticker}", key=f"view_{ticker}", use_container_width=True):
                    st.session_state.selected_ticker = ticker
            with col2:
                if st.button("🗑️", key=f"del_{ticker}"):
                    remove_from_watchlist(ticker)
                    if hasattr(st.session_state, 'selected_ticker') and st.session_state.selected_ticker == ticker:
                        delattr(st.session_state, 'selected_ticker')
                    st.rerun()
    else:
        st.info("Your watchlist is empty. Add some stocks to get started!")

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Main content area
if hasattr(st.session_state, 'selected_ticker') and st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.header(f"📊 {ticker} - Detailed View")

    with st.spinner(f"Loading data for {ticker}..."):
        data, info = get_stock_data(ticker)

        if data is not None:
            # Display stock info
            display_stock_info(info, ticker)

            st.markdown("---")

            # Indicator controls
            st.subheader("Technical Indicators")

            col_ind1, col_ind2, col_ind3, col_ind4 = st.columns(4)

            with col_ind1:
                show_ma = st.checkbox("Show Moving Average", value=False, key="show_ma_checkbox")

            with col_ind2:
                ma_period = st.number_input(
                    "MA Period",
                    min_value=5,
                    max_value=200,
                    value=200,
                    step=5,
                    key="ma_period_input",
                    disabled=not show_ma
                )

            with col_ind3:
                show_rsi = st.checkbox("Show RSI", value=False, key="show_rsi_checkbox")

            with col_ind4:
                rsi_period = st.number_input(
                    "RSI Period",
                    min_value=5,
                    max_value=50,
                    value=14,
                    step=1,
                    key="rsi_period_input",
                    disabled=not show_rsi
                )

            st.markdown("---")

            # Time period selector
            st.subheader("Price Chart")

            # Period selection with tabs
            period_options = {
                "1 Day": ("1d", "line"),
                "1 Week": ("5d", "line"),
                "3 Months": ("3mo", "line"),
                "6 Months": ("6mo", "candlestick"),
                "1 Year": ("1y", "candlestick"),
                "3 Years": ("3y", "candlestick")
            }

            # Create columns for period buttons
            cols = st.columns(len(period_options))

            # Initialize selected period in session state
            if 'selected_period' not in st.session_state:
                st.session_state.selected_period = "1 Year"

            # Period selection buttons
            for idx, (period_name, (period_code, chart_type)) in enumerate(period_options.items()):
                with cols[idx]:
                    if st.button(
                            period_name,
                            key=f"period_{period_name}",
                            type="primary" if st.session_state.selected_period == period_name else "secondary",
                            use_container_width=True
                    ):
                        st.session_state.selected_period = period_name
                        st.rerun()

            # Get selected period details
            selected_period_code, selected_chart_type = period_options[st.session_state.selected_period]

            # Fetch data for selected period
            data_period, _ = get_stock_data(ticker, period=selected_period_code)

            # Create and display chart
            if data_period is not None:
                # Check if we have enough data for MA
                if show_ma and len(data_period) < ma_period:
                    st.warning(
                        f"⚠️ Not enough data points for {ma_period}-period MA. Available: {len(data_period)} points. Try a shorter period or select a longer timeframe.")
                    show_ma_chart = False
                else:
                    show_ma_chart = show_ma

                fig = create_stock_chart(data_period, ticker, chart_type=selected_chart_type,
                                         show_ma=show_ma_chart, ma_period=ma_period)
                st.plotly_chart(fig, use_container_width=True)

                # Show what period is selected
                indicators_active = []
                if show_ma_chart:
                    indicators_active.append(f"{ma_period}-MA")
                if show_rsi:
                    indicators_active.append(f"RSI({rsi_period})")

                caption = f"📊 Showing {st.session_state.selected_period} performance"
                if indicators_active:
                    caption += f" with {', '.join(indicators_active)}"
                st.caption(caption)

                # Display RSI chart if enabled
                if show_rsi:
                    st.markdown("---")
                    rsi_fig, rsi_values = create_rsi_chart(data_period, ticker, rsi_period)
                    st.plotly_chart(rsi_fig, use_container_width=True)

                    # RSI interpretation
                    current_rsi = rsi_values.iloc[-1]
                    if not pd.isna(current_rsi):
                        col_rsi1, col_rsi2, col_rsi3 = st.columns(3)

                        with col_rsi1:
                            st.metric("Current RSI", f"{current_rsi:.2f}")

                        with col_rsi2:
                            if current_rsi > 70:
                                st.metric("Signal", "Overbought ⚠️", delta=None)
                                signal_color = "red"
                            elif current_rsi < 30:
                                st.metric("Signal", "Oversold 📉", delta=None)
                                signal_color = "green"
                            else:
                                st.metric("Signal", "Neutral ➡️", delta=None)
                                signal_color = "gray"

                        with col_rsi3:
                            # Show RSI trend (comparing current vs 5 periods ago)
                            if len(rsi_values) > 5:
                                rsi_change = current_rsi - rsi_values.iloc[-6]
                                st.metric("RSI Trend", f"{current_rsi:.2f}", f"{rsi_change:.2f}")

                        # RSI explanation
                        with st.expander("ℹ️ Understanding RSI"):
                            st.markdown("""
                            **Relative Strength Index (RSI)** is a momentum indicator that measures the speed and magnitude of price changes.

                            - **RSI > 70**: Potentially overbought (price may decrease)
                            - **RSI < 30**: Potentially oversold (price may increase)
                            - **RSI ≈ 50**: Neutral momentum

                            RSI is typically calculated over a 14-period timeframe.
                            """)

                # Moving Average interpretation
                if show_ma_chart and len(data_period) >= ma_period:
                    ma_values = calculate_moving_average(data_period, ma_period)
                    current_price = data_period['Close'].iloc[-1]
                    current_ma = ma_values.iloc[-1]

                    if not pd.isna(current_ma):
                        with st.expander("ℹ️ Moving Average Analysis"):
                            col_ma1, col_ma2 = st.columns(2)

                            with col_ma1:
                                st.metric(f"{ma_period}-Period MA", f"${current_ma:.2f}")
                                price_vs_ma = ((current_price - current_ma) / current_ma) * 100
                                st.metric("Price vs MA", f"{price_vs_ma:+.2f}%")

                            with col_ma2:
                                if current_price > current_ma:
                                    st.success(f"✅ Price is **above** the {ma_period}-MA (Bullish)")
                                else:
                                    st.error(f"⚠️ Price is **below** the {ma_period}-MA (Bearish)")

                            st.markdown(f"""
                            **{ma_period}-Period Moving Average** shows the average closing price over the last {ma_period} periods.

                            - Price above MA: Generally indicates an uptrend
                            - Price below MA: Generally indicates a downtrend
                            - MA slope: Direction indicates trend momentum
                            """)

                # Statistics
                st.markdown("---")
                st.subheader("📊 Statistics")

                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

                with stat_col1:
                    st.metric("Highest Price", f"${data_period['High'].max():.2f}")

                with stat_col2:
                    st.metric("Lowest Price", f"${data_period['Low'].min():.2f}")

                with stat_col3:
                    price_change = data_period['Close'].iloc[-1] - data_period['Close'].iloc[0]
                    price_change_pct = (price_change / data_period['Close'].iloc[0]) * 100
                    st.metric("Period Change", f"${price_change:.2f}", f"{price_change_pct:.2f}%")

                with stat_col4:
                    avg_volume = data_period['Volume'].mean()
                    st.metric("Avg Volume", f"{avg_volume:,.0f}")

                # Recent data table
                st.markdown("---")
                st.subheader("📅 Recent Data")

                # Show different number of rows based on period
                num_rows = min(10, len(data_period))
                recent_data = data_period.tail(num_rows)[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

                # Format date based on period
                if st.session_state.selected_period == "1 Day":
                    recent_data.index = recent_data.index.strftime('%Y-%m-%d %H:%M')
                else:
                    recent_data.index = recent_data.index.strftime('%Y-%m-%d')

                st.dataframe(recent_data.style.format({
                    'Open': '${:.2f}',
                    'High': '${:.2f}',
                    'Low': '${:.2f}',
                    'Close': '${:.2f}',
                    'Volume': '{:,.0f}'
                }), use_container_width=True)
        else:
            st.error(f"Unable to fetch data for {ticker}")

elif st.session_state.watchlist:
    st.header("👋 Welcome to Your Stock Watchlist")
    st.markdown("Select a stock from the sidebar to view detailed charts and information.")

    # Quick overview of all watchlist stocks
    st.subheader("📊 Watchlist Overview")

    overview_data = []
    for ticker in st.session_state.watchlist:
        with st.spinner(f"Loading {ticker}..."):
            data, info = get_stock_data(ticker, period="5d")
            if data is not None and info:
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                prev_close = info.get('previousClose', 0)
                if isinstance(current_price, (int, float)) and isinstance(prev_close, (int, float)):
                    change = current_price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                    overview_data.append({
                        'Ticker': ticker,
                        'Company': info.get('shortName', ticker),
                        'Price': f"${current_price:.2f}",
                        'Change': f"${change:.2f}",
                        'Change %': f"{change_pct:.2f}%",
                        'Volume': f"{info.get('volume', 0):,.0f}"
                    })

    if overview_data:
        df_overview = pd.DataFrame(overview_data)
        st.dataframe(df_overview, use_container_width=True, hide_index=True)
    else:
        st.info("No data available for watchlist stocks")

else:
    st.header("👋 Welcome to Stock Watchlist App")
    st.markdown("""
    ### Get Started

    1. **Add stocks** to your watchlist using the sidebar
    2. **Click on any stock** to view detailed charts and information
    3. **Track performance** with multiple time periods (1D, 1W, 3M, 6M, 1Y, 3Y)
    4. **Enable technical indicators** like Moving Averages and RSI

    ### Features
    - 📈 Real-time stock data
    - 📊 Interactive charts (line charts for short periods, candlestick for longer)
    - 💹 Volume indicators
    - 📉 Multiple time period analysis (1 Day to 3 Years)
    - 📐 **Technical indicators**: Moving Averages (5-200 periods) and RSI
    - 🎯 **Customizable indicators**: Adjust MA and RSI periods
    - 🔄 Easy watchlist management
    - 💾 Persistent watchlist storage

    **Try adding some popular stocks like:** AAPL, GOOGL, MSFT, TSLA, AMZN
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Data provided by Yahoo Finance • Updates in real-time
    </div>
    """,
    unsafe_allow_html=True
)