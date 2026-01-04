"""
Real-Time Stock Market Viewer
==============================
Simple real-time stock viewer using Alpha Vantage API
Shows live updates in a matplotlib window
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
import matplotlib.dates as mdates

# Alpha Vantage API Configuration
API_KEY = "BEWGGWDHQV07D4GG"
BASE_URL = "https://www.alphavantage.co/query"

class RealTimeStockViewer:
    def __init__(self, symbol='AAPL'):
        self.symbol = symbol
        self.df = None
        
        # Create figure and axes
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(14, 8), 
                                                       gridspec_kw={'height_ratios': [3, 1]})
        self.fig.suptitle(f'📈 Real-Time Stock Data: {symbol}', 
                         fontsize=16, fontweight='bold')
        
        # Style the plot
        plt.style.use('dark_background')
        self.fig.patch.set_facecolor('#0f0f1e')
        self.ax1.set_facecolor('#1a1a2e')
        self.ax2.set_facecolor('#1a1a2e')
        
    def fetch_data(self):
        """Fetch real-time data from Alpha Vantage."""
        try:
            # Try intraday first
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': self.symbol,
                'interval': '1min',
                'apikey': API_KEY,
                'outputsize': 'compact'
            }
            
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (1min)' in data:
                time_series = data['Time Series (1min)']
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
                
                return df
            
            # If intraday fails, try daily
            params['function'] = 'TIME_SERIES_DAILY'
            params.pop('interval', None)
            
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
                
                return df
            
            return None
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def update(self, frame):
        """Update the plot with new data."""
        if frame % 6 == 0:  # Fetch every 6th frame (every minute if interval is 10s)
            print(f"Fetching data... ({datetime.now().strftime('%H:%M:%S')})")
            new_df = self.fetch_data()
            
            if new_df is not None:
                self.df = new_df
        
        if self.df is None or self.df.empty:
            return
        
        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        
        # Plot price
        self.ax1.plot(self.df.index, self.df['close'], 
                     color='#00ff88', linewidth=2, label='Close Price')
        self.ax1.plot(self.df.index, self.df['open'], 
                     color='#667eea', linewidth=1, alpha=0.6, label='Open Price')
        
        # Add moving average if enough data
        if len(self.df) >= 20:
            ma20 = self.df['close'].rolling(window=20).mean()
            self.ax1.plot(self.df.index, ma20, 
                         color='#ffd700', linewidth=2, linestyle='--', label='MA(20)')
        
        # Fill between high and low
        self.ax1.fill_between(self.df.index, self.df['low'], self.df['high'], 
                             alpha=0.2, color='#667eea')
        
        # Plot volume
        colors = ['#00ff88' if close >= open else '#ff0055' 
                 for close, open in zip(self.df['close'], self.df['open'])]
        self.ax2.bar(self.df.index, self.df['volume'], 
                    color=colors, alpha=0.7, width=0.0008)
        
        # Format axes
        self.ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        self.ax1.legend(loc='upper left', framealpha=0.8)
        self.ax1.grid(True, alpha=0.3, linestyle='--')
        
        self.ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
        self.ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
        self.ax2.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis dates
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Rotate x-axis labels
        plt.setp(self.ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add current price annotation
        if not self.df.empty:
            current_price = self.df['close'].iloc[-1]
            open_price = self.df['open'].iloc[0]
            change = current_price - open_price
            change_pct = (change / open_price) * 100
            
            color = '#00ff88' if change >= 0 else '#ff0055'
            
            self.ax1.text(0.02, 0.98, 
                         f'Current: ${current_price:.2f}\n'
                         f'Change: {change:+.2f} ({change_pct:+.2f}%)\n'
                         f'High: ${self.df["high"].max():.2f}\n'
                         f'Low: ${self.df["low"].min():.2f}',
                         transform=self.ax1.transAxes,
                         verticalalignment='top',
                         bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                         fontsize=11,
                         color=color,
                         fontweight='bold')
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.fig.text(0.99, 0.01, f'Last updated: {timestamp}',
                     ha='right', va='bottom', fontsize=9, color='gray')
        
        plt.tight_layout()
    
    def start(self):
        """Start the real-time visualization."""
        print(f"Starting real-time viewer for {self.symbol}...")
        print("Fetching initial data...")
        
        self.df = self.fetch_data()
        
        if self.df is None:
            print("Error: Could not fetch initial data")
            return
        
        print(f"Loaded {len(self.df)} data points")
        print("Starting animation... (Close the window to exit)")
        
        # Create animation (update every 10 seconds)
        anim = FuncAnimation(self.fig, self.update, 
                           interval=10000, cache_frame_data=False)
        
        plt.show()


def main():
    """Main function."""
    print("=" * 50)
    print("Real-Time Stock Market Viewer")
    print("=" * 50)
    print()
    
    # Get stock symbol from user
    symbol = input("Enter stock symbol (default: AAPL): ").strip().upper()
    if not symbol:
        symbol = 'AAPL'
    
    print(f"\nLaunching viewer for {symbol}...")
    print("Note: API updates may take ~60 seconds due to rate limits")
    print()
    
    viewer = RealTimeStockViewer(symbol)
    viewer.start()


if __name__ == "__main__":
    main()
