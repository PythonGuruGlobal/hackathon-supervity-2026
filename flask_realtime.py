"""
Real-Time Stock Market Web Dashboard
=====================================
Simple Flask-based dashboard with live stock data
No heavy dependencies required
"""

from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import json

app = Flask(__name__)

# Alpha Vantage API Configuration
API_KEY = "BEWGGWDHQV07D4GG"
BASE_URL = "https://www.alphavantage.co/query"

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """Fetch stock data from Alpha Vantage API."""
    try:
        # Try intraday data first
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol.upper(),
            'interval': '1min',
            'apikey': API_KEY,
            'outputsize': 'compact'
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (1min)' in data:
            time_series = data['Time Series (1min)']
            
            # Convert to list format
            stock_data = []
            for timestamp, values in sorted(time_series.items()):
                stock_data.append({
                    'time': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'data': stock_data,
                'timestamp': datetime.now().isoformat()
            })
        
        # Try daily data if intraday fails
        params['function'] = 'TIME_SERIES_DAILY'
        params.pop('interval', None)
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            
            stock_data = []
            for timestamp, values in sorted(time_series.items())[-100:]:
                stock_data.append({
                    'time': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'data': stock_data,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': False,
            'error': data.get('Note', data.get('Error Message', 'Unknown error'))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Real-Time Stock Market Dashboard")
    print("=" * 60)
    print("\n✅ Server starting...")
    print("📊 Dashboard will open at: http://localhost:5000")
    print("🔄 Auto-refresh enabled (60 seconds)")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
