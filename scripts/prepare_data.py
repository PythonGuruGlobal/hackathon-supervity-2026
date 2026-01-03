"""
Prepare stock data for agent analysis
"""
import pandas as pd

# Load full dataset
df = pd.read_csv('../stock_market_dataset.csv')

# Filter for AAPL only
aapl = df[df['Stock'] == 'AAPL'].copy()

# Sort by date
aapl = aapl.sort_values('Date').reset_index(drop=True)

# Select only the columns we need (OHLCV format)
aapl_clean = aapl[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()

# Take the last 100 days for analysis
aapl_recent = aapl_clean.tail(100)

# Save to data folder
output_path = '../data/aapl_recent.csv'
aapl_recent.to_csv(output_path, index=False)

print(f"✓ Prepared AAPL data: {len(aapl_recent)} days")
print(f"  Date range: {aapl_recent['Date'].min()} to {aapl_recent['Date'].max()}")
print(f"  Saved to: {output_path}")
print()

# Show last few days to see the pattern
print("Last 10 days of data:")
print(aapl_recent.tail(10).to_string(index=False))
