"""
Comprehensive Real-Time Stock Market Dashboard with Agentic Alerts
===================================================================
Combines historical dataset + live API data with full alert agent system

Run with: python comprehensive_dashboard.py
"""

from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import json

# Pure Python implementations without numpy/pandas
class SimpleForecaster:
    """Pure Python forecaster without numpy dependencies."""
    def __init__(self, window=10):
        self.window = window
        self.fitted = False
        self.data = None
    
    def fit(self, data, target_col="close"):
        """Fit forecaster to data."""
        self.data = data
        self.fitted = True
    
    def forecast(self, steps=1):
        """Simple forecast using moving average."""
        if not self.fitted or not self.data:
            return {'predicted_value': 0, 'lower_bound': 0, 'upper_bound': 0, 'confidence': 0}
        
        # Get recent prices
        prices = [float(d['close']) for d in self.data[-self.window:]]
        
        # Calculate moving average
        avg = sum(prices) / len(prices)
        
        # Calculate simple trend
        if len(prices) >= 2:
            recent_change = (prices[-1] - prices[0]) / len(prices)
            predicted = avg + (recent_change * steps)
        else:
            predicted = avg
        
        # Calculate volatility (standard deviation)
        mean = sum(prices) / len(prices)
        variance = sum((x - mean) ** 2 for x in prices) / len(prices)
        std = variance ** 0.5
        
        return {
            'predicted_value': predicted,
            'lower_bound': predicted - (1.96 * std),
            'upper_bound': predicted + (1.96 * std),
            'confidence': 0.85
        }

class AlertAgent:
    """Pure Python alert agent."""
    def __init__(self, price_drop_threshold=3.0, price_spike_threshold=4.0, 
                 volatility_threshold=0.025, min_confidence_threshold=0.6, **kwargs):
        self.price_drop_threshold = price_drop_threshold
        self.price_spike_threshold = price_spike_threshold
        self.volatility_threshold = volatility_threshold
    
    def evaluate(self, metrics, forecast_confidence=0.95):
        """Evaluate metrics and return alert decision."""
        class Decision:
            def __init__(self):
                self.should_alert = False
                self.alert_type = "none"
                self.confidence = "medium"
                self.reason = "No alerts detected"
                self.metrics = metrics
        
        decision = Decision()
        
        # Check for price drop
        if metrics.get('price_change_pct', 0) < -self.price_drop_threshold:
            decision.should_alert = True
            decision.alert_type = "PRICE_DROP"
            decision.confidence = "high"
            decision.reason = f"Price predicted to drop by {abs(metrics['price_change_pct']):.2f}%"
        
        # Check for price spike
        elif metrics.get('price_change_pct', 0) > self.price_spike_threshold:
            decision.should_alert = True
            decision.alert_type = "PRICE_SPIKE"
            decision.confidence = "high"
            decision.reason = f"Price predicted to rise by {metrics['price_change_pct']:.2f}%"
        
        # Check for high volatility
        elif metrics.get('volatility', 0) > self.volatility_threshold:
            decision.should_alert = True
            decision.alert_type = "VOLATILITY_SPIKE"
            decision.confidence = "medium"
            decision.reason = f"High volatility detected: {metrics['volatility']*100:.2f}%"
        
        return decision

app = Flask(__name__)

# Alpha Vantage API Configuration
API_KEY = "BEWGGWDHQV07D4GG"
BASE_URL = "https://www.alphavantage.co/query"

# Initialize forecaster and agent
forecaster = SimpleForecaster(window=10)
alert_agent = AlertAgent(
    price_drop_threshold=3.0,
    price_spike_threshold=4.0,
    volatility_threshold=0.025,
    min_confidence_threshold=0.6
)

# Store alerts
alerts_history = []


def load_dataset_stocks():
    """Load available stocks from dataset."""
    try:
        import csv
        stocks = set()
        with open('stock_market_dataset.csv', 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i > 100:  # Sample first 100 rows
                    break
                stocks.add(row['Stock'])
        return sorted(list(stocks))
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']


def load_historical_data(symbol, limit=100):
    """Load historical data from dataset."""
    try:
        import csv
        data = []
        with open('stock_market_dataset.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Stock'] == symbol:
                    data.append({
                        'time': row['Date'],
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(float(row['Volume']))
                    })
        return data[-limit:] if len(data) > limit else data
    except Exception as e:
        print(f"Error loading historical data: {e}")
        return []


def fetch_live_data(symbol):
    """Fetch live data from Alpha Vantage API."""
    try:
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol.upper(),
            'interval': '5min',
            'apikey': API_KEY,
            'outputsize': 'compact'
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (5min)' in data:
            time_series = data['Time Series (5min)']
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
            return stock_data, None
        
        # Try daily if intraday fails
        params['function'] = 'TIME_SERIES_DAILY'
        params.pop('interval', None)
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            stock_data = []
            for timestamp, values in sorted(time_series.items())[-50:]:
                stock_data.append({
                    'time': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            return stock_data, None
        
        return None, data.get('Note', data.get('Error Message', 'Unknown error'))
        
    except Exception as e:
        return None, str(e)


def analyze_with_agent(data):
    """Analyze data and generate alerts using agent system."""
    try:
        if len(data) < 10:
            return None
        
        # Prepare data for forecaster
        class DataWrapper:
            def __init__(self, data):
                self.data = data
            
            def __getitem__(self, key):
                if key == 'Close':
                    return [d['close'] for d in self.data]
                return [d[key.lower()] for d in self.data]
            
            def iloc(self):
                return self
        
        # Fit forecaster
        forecaster.fit(data, target_col='close')
        forecast = forecaster.forecast(steps=1)
        
        # Calculate metrics
        last_close = data[-1]['close']
        predicted = forecast['predicted_value']
        change_pct = ((predicted - last_close) / last_close) * 100
        
        # Calculate volatility
        if len(data) >= 10:
            closes = [d['close'] for d in data[-10:]]
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            volatility = (sum([r**2 for r in returns]) / len(returns)) ** 0.5
        else:
            volatility = 0.01
        
        metrics = {
            'price_change_pct': change_pct,
            'volatility': volatility,
            'last_close': last_close,
            'predicted_price': predicted,
            'confidence': forecast['confidence']
        }
        
        # Get agent decision
        decision = alert_agent.evaluate(metrics, forecast['confidence'])
        
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'should_alert': decision.should_alert,
            'alert_type': str(decision.alert_type) if hasattr(decision.alert_type, 'value') else str(decision.alert_type),
            'confidence': str(decision.confidence) if hasattr(decision.confidence, 'value') else str(decision.confidence),
            'reason': decision.reason,
            'metrics': metrics,
            'forecast': forecast
        }
        
        if decision.should_alert:
            alerts_history.append(alert_data)
        
        return alert_data
        
    except Exception as e:
        print(f"Error in agent analysis: {e}")
        return None


@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('comprehensive_dashboard.html')


@app.route('/api/dataset/stocks')
def get_dataset_stocks():
    """Get list of stocks from dataset."""
    stocks = load_dataset_stocks()
    return jsonify({'success': True, 'stocks': stocks})


@app.route('/api/stock/<symbol>/historical')
def get_historical_data(symbol):
    """Get historical data from dataset."""
    data = load_historical_data(symbol.upper())
    
    if data:
        # Analyze with agent
        alert = analyze_with_agent(data)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'source': 'dataset',
            'data': data,
            'alert': alert,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'error': f'No historical data found for {symbol}'
        })


@app.route('/api/stock/<symbol>/live')
def get_live_data(symbol):
    """Get live data from API."""
    data, error = fetch_live_data(symbol.upper())
    
    if error:
        return jsonify({'success': False, 'error': error})
    
    if data:
        # Analyze with agent
        alert = analyze_with_agent(data)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'source': 'live_api',
            'data': data,
            'alert': alert,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No data available'
        })


@app.route('/api/alerts')
def get_alerts():
    """Get all alerts."""
    return jsonify({
        'success': True,
        'alerts': alerts_history[-50:],  # Last 50 alerts
        'count': len(alerts_history)
    })


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 COMPREHENSIVE STOCK MARKET DASHBOARD WITH AGENTIC ALERTS")
    print("=" * 70)
    print("\n✅ Features:")
    print("   📊 Historical Dataset Stocks")
    print("   🔴 Live API Data (Alpha Vantage)")
    print("   🤖 Agentic Alert System")
    print("   📈 Real-time Forecasting")
    print("   ⚡ Intelligent Decision Making")
    print(f"\n🌐 Dashboard: http://localhost:5001")
    print("🔄 Auto-refresh: 60 seconds")
    print("\n⌨️  Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
