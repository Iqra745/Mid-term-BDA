# -*- coding: utf-8 -*-
"""BDA Mid ETL Pipeline.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zLS7EMkhtaseTQGfSYi98N49zxm-3BiS

# ✅ Handling Variations in Data Formats and Units
Real-world datasets, especially from different sources like MarketStack and Kaggle, often vary in format, units, and structure. The pipeline you built addresses these issues in multiple steps:

## 1. Date and Timestamp Normalization
Problem: MarketStack and Kaggle datasets might have timestamps in different formats (datetime, string, with or without timezones).

Solution:

standardize_timestamps() converts date columns to timezone-aware datetime objects using pd.to_datetime(..., utc=True).

Filters data to focus on the relevant year (2025), ensuring consistency and relevance.

## 2. Column Name Standardization
Problem: Inconsistent column naming due to formatting (spaces, capital letters).

Solution:

normalize_column_names() makes all column names lowercase and replaces spaces with underscores for uniformity.

## 3. Handling Missing or Corrupted Data
Problem: Missing values can skew analysis or lead to runtime errors.

Solution:

check_for_null_values() identifies null columns in both datasets.

handle_missing_values() fills or derives missing columns like capital_gains as needed.

## 4. Validating and Cleaning Financial Values
Problem: Negative or invalid values in stock prices, volume, etc.

Solution:

validate_data() removes rows where key numeric fields (open, close, volume, etc.) are negative.

## 5. Harmonizing Feature Sets
Problem: Some datasets may not contain calculated features like return or volatility.

Solution:

add_features() adds daily_return = (close - open)/open and volatility = high - low for both datasets to ensure consistent analysis.

## 6. Merging and Deduplication
Problem: Different datasets might overlap in time or ticker coverage.

Solution:

merge_datasets() combines both datasets and removes duplicates based on symbol + date.

## 📊 Using the Final DataFrame for Deeper Analysis
After transformation, the resulting clean and enriched DataFrame is ideal for trend and pattern analysis in stock market behavior.

Here’s how:

✅ Time-Series Analysis
date_only allows easy grouping and visualization over time.

Analyze how each stock's open, close, or volume changed daily.

✅ Volatility and Risk Insights
Use the volatility feature to understand how risky or stable a stock is over time.

Plot volatility spikes to identify key market events.

✅ Returns and Profitability
daily_return helps detect high-performing stocks or downtrends.

Combine this with moving averages or cumulative returns to track investment performance.

✅ Volume-Based Insights
volume helps detect surges in market interest or trading activity, which often precede price moves.

✅ Comparative Analysis Across Companies
With consistent symbol and metrics, you can compare AAPL vs MSFT or other tickers on:

Average daily return

Price movement volatility

Trading volume

✅ Machine Learning & Forecasting Ready
The cleaned DataFrame can directly feed into:

Forecasting models (ARIMA, LSTM, Prophet)

Classification (e.g., predicting up/down movement)

Clustering (e.g., grouping similar stock behaviors)

🔁 Example Use Cases:
Investor Insight Dashboard: Daily returns and volume trends.

Risk Assessment Tool: Monitor volatility of holdings.

Backtesting Engine: Simulate trading strategies using historical open, close.

Would you like me to create some visualizations next (e.g., daily return trends, volatility heatmaps, or moving averages)?
"""

!pip install pandas requests kagglehub[pandas-datasets] pymongo

import requests
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter
from pymongo import MongoClient
import matplotlib.pyplot as plt
import seaborn as sns

def get_data_from_kaggle_df():
        """
        Connector # 2
        Load stock data from Kaggle dataset using KaggleHub.
        """
        file_path = "World-Stock-Prices-Dataset.csv"
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "nelgiriyewithana/world-stock-prices-daily-updating",
            file_path
        )
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df = df[df['Date'].dt.year == 2022]
        # Save to CSV
        df.to_csv("filtered_2022_stock_data.csv", index=False)

        # Trigger download in Colab
        files.download("filtered_2022_stock_data.csv")
        return df

class ETLPipeline:
    """
    A class for collecting, transforming, analyzing, and loading financial stock data
    from MarketStack API and Kaggle datasets.
    """

    # API and configuration constants
    ticker_url = 'https://gist.githubusercontent.com/rayyanali00/a311644d6d902100242345d1198a7a53/raw/tickers.json'
    marketstack_baseapiurl = 'https://api.marketstack.com/v2/eod?access_key=580c67effd676378137d18d392f35603'
    marketstack_apiurlgist = 'https://gist.githubusercontent.com/rayyanali00/ec7fa991d7bb93d51a786ae811563ebc/raw/marketstack_stockdata.json'
    datefrom = '2025-03-01'
    dateto = '2025-04-01'
    IS_MOCK = True

    def __init__(self, datefrom=None, dateto=None):
        """Initialize DataCollection with optional custom date range."""
        if datefrom and dateto:
            self.datefrom = datefrom
            self.dateto = dateto

    def api_request(self, requesturl):
        """Generic method to make API requests."""
        data = requests.get(requesturl)
        return data.json()

    def get_tickers(self):
        """Fetch the list of tickers from the provided ticker URL."""
        tickers_json = self.api_request(self.ticker_url)
        data = tickers_json['data'][:25]
        tickers_list = [x['ticker'] for x in data]
        return tickers_list

    def get_stock_data_from_marketstack(self):
        """Fetch historical stock data either from MarketStack API or a mock source."""
        tickers_list = self.get_tickers()
        tickers_str = ','.join(tickers_list)
        if self.IS_MOCK:
            marketstack_url = self.marketstack_apiurlgist
        else:
            marketstack_url = f'{self.marketstack_baseapiurl}&symbols={tickers_str}&date_from={self.datefrom}&date_to={self.dateto}'
        stock_data = self.api_request(marketstack_url)['data']
        df = pd.DataFrame(stock_data)
        return df

    def get_data_from_kaggle_df(self):
        """Load stock data from Kaggle dataset using KaggleHub."""
        file_path = "World-Stock-Prices-Dataset.csv"
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "nelgiriyewithana/world-stock-prices-daily-updating",
            file_path
        )
        return df



    def check_for_null_values(self):
        """Check and return columns with null values in both datasets."""
        marketstack_df = self.get_stock_data_from_marketstack()
        kaggle_df = self.get_data_from_kaggle_df()

        marketstack_nulls = marketstack_df.isnull().sum()
        kaggle_nulls = kaggle_df.isnull().sum()

        marketstack_null_cols = {col: count for col, count in marketstack_nulls.items() if count > 0}
        kaggle_null_cols = {col: count for col, count in kaggle_nulls.items() if count > 0}

        print("Null values in MarketStack DataFrame:", marketstack_null_cols)
        print("Null values in Kaggle DataFrame:", kaggle_null_cols)

        return {
            "marketstack_nulls": marketstack_null_cols,
            "kaggle_nulls": kaggle_null_cols
        }

    def handle_missing_values(self, kaggle_df):
        """Add capital gains feature (close - open) to Kaggle data."""
        kaggle_df['capital_gains'] = kaggle_df['close'] - kaggle_df['open']
        return kaggle_df

    def normalize_column_names(self, df):
        """Normalize column names to lowercase and underscores."""
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        return df

    def validate_data(self, df):
        """Drop rows with invalid (negative) financial values."""
        numeric_cols = ['open', 'close', 'high', 'low', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df = df[df[col] >= 0]
        return df

    def add_features(self, df):
        """Calculate daily return and volatility as new features."""
        if {'close', 'open', 'high', 'low'}.issubset(df.columns):
            df['daily_return'] = (df['close'] - df['open']) / df['open']
            df['volatility'] = df['high'] - df['low']
        return df

    def aggregate_data(self, df, date_col='date', groupby_col='symbol', company='name'):
        """Aggregate financial metrics by ticker and date."""
        df[date_col] = pd.to_datetime(df[date_col])
        df['date_only'] = df[date_col].dt.date
        grouped = df.groupby([groupby_col, 'date_only']).agg({
            'open': 'mean',
            'close': 'mean',
            'high': 'max',
            'low': 'min',
            'volume': 'sum',
            'daily_return': 'mean',
            'volatility': 'mean'
        }).reset_index()
        return grouped

    def standardize_timestamps(self, market_df, kaggle_df):
        """Convert date columns to datetime and filter data for year 2025."""
        market_df['date'] = pd.to_datetime(market_df['date'], utc=True)
        kaggle_df['Date'] = pd.to_datetime(kaggle_df['Date'], utc=True)
        market_df = market_df[market_df['date'].dt.year == 2025]
        kaggle_df = kaggle_df[kaggle_df['Date'].dt.year == 2025]
        return market_df, kaggle_df

    def merge_datasets(self, market_agg, kaggle_agg):
        """Merge MarketStack and Kaggle data, dropping duplicates on symbol + date."""
        combined_df = pd.concat([market_agg, kaggle_agg], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['symbol', 'date_only'], keep='first')
        return combined_df

    def run_transformation(self):
        """
        Runs the full ETL transformation pipeline:
        1. Load data
        2. Normalize and validate
        3. Feature engineering
        4. Aggregation and merging
        """
        # Step 1: Load
        market_df = self.get_stock_data_from_marketstack()
        kaggle_df = self.get_data_from_kaggle_df()

        # Step 2: Filter for 2025 and clean date formats
        market_df, kaggle_df = self.standardize_timestamps(market_df, kaggle_df)

        # Fix case issues in brand names
        kaggle_df['Brand_Name'] = kaggle_df['Brand_Name'].str.title()

        # Step 3: Normalize column names
        market_df = self.normalize_column_names(market_df)
        kaggle_df = self.normalize_column_names(kaggle_df)

        # Step 4: Handle missing data
        kaggle_df = self.handle_missing_values(kaggle_df)

        # Step 5: Validate
        market_df = self.validate_data(market_df)
        kaggle_df = self.validate_data(kaggle_df)

        # Step 6: Feature engineering
        market_df = self.add_features(market_df)
        kaggle_df = self.add_features(kaggle_df)

        # Step 7: Aggregate by date and symbol
        market_agg = self.aggregate_data(market_df)
        kaggle_agg = self.aggregate_data(kaggle_df, date_col='date', groupby_col='ticker', company='brand_name')
        kaggle_agg = kaggle_agg.rename(columns={'ticker': 'symbol'})

        # Step 8: Merge
        print(market_agg.shape)
        print(kaggle_agg.shape)
        merged_df = self.merge_datasets(market_agg, kaggle_agg)
        return merged_df

    def plot_daily_return_distribution(self, df):
      """
      Plots a histogram of the daily return distribution for all stocks.

      Parameters:
      df (DataFrame): DataFrame containing stock data with 'daily_return' column.
      """
      plt.figure(figsize=(10, 6))
      sns.histplot(df['daily_return'], bins=50, kde=True, color='blue')
      plt.title('Distribution of Daily Returns', fontsize=16)
      plt.xlabel('Daily Return', fontsize=12)
      plt.ylabel('Frequency', fontsize=12)
      plt.show()

    def plot_stock_price_vs_volume(self, df):
      """
      Plots a scatter plot between stock price (close) and trading volume.

      Parameters:
      df (DataFrame): DataFrame containing stock data with 'close' and 'volume' columns.
      """
      plt.figure(figsize=(10, 6))
      sns.scatterplot(data=df, x='close', y='volume', hue='symbol', palette='tab10', size='volume', sizes=(20, 200))
      plt.title('Stock Price vs Trading Volume', fontsize=16)
      plt.xlabel('Closing Price', fontsize=12)
      plt.ylabel('Volume', fontsize=12)
      plt.show()

    def plot_volatility_over_time(self, df):
      """
      Plots the volatility (high-low) over time for each stock.

      Parameters:
      df (DataFrame): DataFrame containing stock data with 'date_only', 'symbol', and 'volatility' columns.
      """
      plt.figure(figsize=(10, 6))
      for symbol in df['symbol'].unique():
          symbol_data = df[df['symbol'] == symbol]
          plt.plot(symbol_data['date_only'], symbol_data['volatility'], label=symbol)

      plt.title('Volatility Over Time by Stock', fontsize=16)
      plt.xlabel('Date', fontsize=12)
      plt.ylabel('Volatility', fontsize=12)
      plt.legend(title='Symbol')
      plt.xticks(rotation=45)
      plt.tight_layout()
      plt.show()

    def plot_average_daily_return(self, df):
      """
      Plots a bar chart of average daily return by stock.

      Parameters:
      df (DataFrame): DataFrame containing stock data with 'symbol' and 'daily_return' columns.
      """
      average_return = df.groupby('symbol')['daily_return'].mean().sort_values(ascending=False)

      plt.figure(figsize=(10, 6))
      average_return.plot(kind='bar', color='orange')
      plt.title('Average Daily Return by Stock', fontsize=16)
      plt.xlabel('Stock Symbol', fontsize=12)
      plt.ylabel('Average Daily Return', fontsize=12)
      plt.xticks(rotation=45)
      plt.tight_layout()
      plt.show()

    def plot_stock_prices_over_time(self, df):
      """
      Plots stock prices (closing prices) over time for multiple stocks.

      Parameters:
      df (DataFrame): DataFrame containing stock data with 'date_only', 'symbol', and 'close' columns.
      """
      plt.figure(figsize=(10, 6))
      for symbol in df['symbol'].unique():
          symbol_data = df[df['symbol'] == symbol]
          plt.plot(symbol_data['date_only'], symbol_data['close'], label=symbol)

      plt.title('Stock Prices Over Time for Multiple Stocks', fontsize=16)
      plt.xlabel('Date', fontsize=12)
      plt.ylabel('Closing Price', fontsize=12)
      plt.legend(title='Symbol')
      plt.xticks(rotation=45)
      plt.tight_layout()
      plt.show()


    def load_data(self, df):
        """
        Load final processed data to MongoDB.
        Converts date to datetime to avoid BSON encoding errors.
        """
        df['date_only'] = pd.to_datetime(df['date_only'])
        mongoclient = MongoClient('mongodb+srv://rayyanned_db1:rayyan123@cluster-ned.3frsh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster-NED')
        db = mongoclient['financial_stock']
        collection = db['stocksdata']

        records = df.to_dict(orient='records')

        if records:
            collection.insert_many(records)
            print(f"Inserted {len(records)} documents into collection.")
        else:
            print("No records to insert.")

data_collection = DataCollection()

df = data_collection.run_transformation()

data_collection.plot_volatility_over_time(df)

# data_collection.load_data(df)

df



