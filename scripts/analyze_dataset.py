import pandas as pd

# Load dataset
df = pd.read_csv('../stock_market_dataset.csv')

print(f'Total rows: {len(df)}')
print(f'Unique stocks: {df["Stock"].nunique()}')
print(f'Date range: {df["Date"].min()} to {df["Date"].max()}')
print(f'\nColumns: {list(df.columns)}')

print(f'\nStocks in dataset: {sorted(df["Stock"].unique())}')

# Show sample data for AAPL
print(f'\nSample data for AAPL:')
aapl = df[df['Stock']=='AAPL'].head(20)
print(aapl[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']])
