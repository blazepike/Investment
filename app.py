import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import os

# Ensure required packages are installed
try:
    import plotly
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "plotly"])
    import plotly.graph_objects as go

# Alpha Vantage API Key from environment variables
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Function to fetch stock data
def fetch_stock_price(symbol):
    url = f"{BASE_URL}?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={API_KEY}&outputsize=compact"
    response = requests.get(url).json()
    time_series = response.get("Time Series (Daily)", {})
    df = pd.DataFrame(time_series).T.rename(columns={
        "1. open": "Open", "2. high": "High", "3. low": "Low", "4. close": "Close", "5. adjusted close": "Adj Close"
    })
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    return df

# Function to fetch company overview
def fetch_company_overview(symbol):
    url = f"{BASE_URL}?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url).json()
    return response

# Streamlit UI
st.title("Investment Portfolio Tracker")

# Sidebar: Portfolio Management
st.sidebar.header("Manage Portfolio")

if "portfolio" not in st.session_state:
    st.session_state["portfolio"] = []

symbol = st.sidebar.text_input("Stock Symbol")
units = st.sidebar.number_input("Units", min_value=0, step=1)
purchase_price = st.sidebar.number_input("Purchase Price", min_value=0.0, step=0.1)

if st.sidebar.button("Add to Portfolio"):
    if symbol and units > 0 and purchase_price > 0:
        st.session_state["portfolio"].append({"Symbol": symbol.upper(), "Units": units, "Purchase Price": purchase_price})
        st.sidebar.success(f"Added {symbol.upper()} to portfolio.")
    else:
        st.sidebar.error("Please enter valid stock details.")

if st.sidebar.button("Clear Portfolio"):
    st.session_state["portfolio"] = []
    st.sidebar.success("Portfolio cleared.")

# Portfolio Table
df_portfolio = pd.DataFrame(st.session_state["portfolio"])
if not df_portfolio.empty:
    st.subheader("Current Portfolio")
    st.dataframe(df_portfolio)
    
    # Fetch latest prices
    prices = {row["Symbol"]: fetch_stock_price(row["Symbol"]).iloc[0]["Adj Close"] for _, row in df_portfolio.iterrows()}
    df_portfolio["Current Price"] = df_portfolio["Symbol"].map(prices)
    df_portfolio["Value"] = df_portfolio["Units"] * df_portfolio["Current Price"]
    
    # Portfolio Value
    total_value = df_portfolio["Value"].sum()
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
    
    # Portfolio Breakdown
    fig_pie = go.Figure(data=[go.Pie(labels=df_portfolio["Symbol"], values=df_portfolio["Value"], title="Portfolio Allocation")])
    st.plotly_chart(fig_pie)

    # Fetch sector information dynamically
    industries = {row["Symbol"]: fetch_company_overview(row["Symbol"]).get("Sector", "Unknown") for _, row in df_portfolio.iterrows()}
    df_portfolio["Industry"] = df_portfolio["Symbol"].map(industries)
    
    fig_bar = go.Figure(data=[go.Bar(x=df_portfolio["Industry"], y=df_portfolio["Value"], text=df_portfolio["Value"], textposition='auto')])
    fig_bar.update_layout(title="Sector Exposure")
    st.plotly_chart(fig_bar)

# Company Health Analysis
st.subheader("Company Health Overview")
selected_stock = st.selectbox("Select a Stock", df_portfolio["Symbol"] if not df_portfolio.empty else [])
if selected_stock:
    company_data = fetch_company_overview(selected_stock)
    st.write(f"### {company_data.get('Name', 'Unknown')} ({selected_stock})")
    st.write(f"**Industry:** {company_data.get('Industry', 'N/A')}")
    st.write(f"**Revenue:** ${company_data.get('RevenueTTM', 'N/A')}")
    st.write(f"**Profit Margin:** {company_data.get('ProfitMargin', 'N/A')}%")
    st.write(f"**Free Cash Flow:** ${company_data.get('OperatingCashflow', 'N/A')}")
