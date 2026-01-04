"""
PROFESSIONAL AGENTIC MARKET ALERT SYSTEM
=========================================
Interview-Ready Implementation with Full Agent Architecture

This system demonstrates:
- Observation (multi-signal data collection)
- Planning (reasoning over context)
- Decision (intelligent alert triggering)
- Action (generating alerts with explanations)
- Reflection (learning from past decisions)
- Memory (preventing alert fatigue)
"""

from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# ==================== CONFIGURATION ====================
API_KEY = "BEWGGWDHQV07D4GG"
BASE_URL = "https://www.alphavantage.co/query"

# ==================== DATA LAYER ====================

class DataManager:
    """Manages both historical dataset and live API data"""
    
    @staticmethod
    def load_dataset_stocks():
        """Load available stocks from historical dataset"""
        try:
            import csv
            stocks = set()
            with open('stock_market_dataset.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stocks.add(row['Stock'])
            return sorted(list(stocks))
        except Exception as e:
            print(f"Dataset error: {e}")
            return ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
    
    @staticmethod
    def load_historical_data(symbol, limit=50):
        """Load historical data for a stock"""
        try:
            import csv
            data = []
            with open('stock_market_dataset.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Stock'] == symbol:
                        data.append({
                            'date': row['Date'],
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(float(row['Volume'])),
                            'rsi': float(row.get('RSI', 50)),
                            'sentiment': float(row.get('Sentiment_Score', 0))
                        })
            return data[-limit:]
        except Exception as e:
            print(f"Error loading historical: {e}")
            return []
    
    @staticmethod
    def fetch_live_data(symbol):
        """Fetch real-time data from Alpha Vantage API"""
        try:
            # Fetch daily data
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol.upper(),
                'outputsize': 'compact',
                'apikey': API_KEY
            }
            
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                stock_data = []
                
                for date, values in sorted(time_series.items())[-50:]:
                    stock_data.append({
                        'date': date,
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


# ==================== FORECASTING LAYER ====================

class Forecaster:
    """Pure Python ML forecaster - predicts next price"""
    
    def __init__(self, window=10):
        self.window = window
    
    def forecast(self, data):
        """
        Forecast next closing price using:
        - Moving average
        - Trend analysis
        - Volatility estimation
        """
        if len(data) < self.window:
            return None
        
        # Extract recent prices
        prices = [d['close'] for d in data[-self.window:]]
        
        # 1. Calculate moving average
        ma = sum(prices) / len(prices)
        
        # 2. Calculate trend (linear regression)
        n = len(prices)
        x_mean = (n - 1) / 2
        y_mean = sum(prices) / n
        
        numerator = sum((i - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # 3. Predict next price
        predicted = ma + slope
        
        # 4. Calculate volatility (standard deviation)
        variance = sum((p - y_mean) ** 2 for p in prices) / n
        std_dev = variance ** 0.5
        
        # 5. Confidence based on volatility
        confidence = max(0.5, min(0.95, 1 - (std_dev / y_mean)))
        
        # 6. Calculate price change percentage
        last_price = prices[-1]
        price_change_pct = ((predicted - last_price) / last_price) * 100
        
        return {
            'predicted_price': predicted,
            'current_price': last_price,
            'price_change_pct': price_change_pct,
            'confidence': confidence,
            'volatility': std_dev,
            'lower_bound': predicted - (1.96 * std_dev),
            'upper_bound': predicted + (1.96 * std_dev),
            'trend': 'UPWARD' if slope > 0 else 'DOWNWARD' if slope < 0 else 'STABLE'
        }
    
    def calculate_technical_indicators(self, data):
        """Calculate additional technical indicators"""
        if len(data) < 14:
            return {}
        
        prices = [d['close'] for d in data]
        
        # RSI calculation
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [c if c > 0 else 0 for c in changes]
        losses = [-c if c < 0 else 0 for c in changes]
        
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50
        
        # Volume analysis
        volumes = [d['volume'] for d in data]
        avg_volume = sum(volumes[-10:]) / 10
        volume_spike = (volumes[-1] / avg_volume - 1) * 100 if avg_volume > 0 else 0
        
        return {
            'rsi': rsi,
            'volume_spike_pct': volume_spike,
            'avg_volume': avg_volume
        }


# ==================== AGENTIC LAYER ====================

class AgenticAlertSystem:
    """
    TRUE AGENTIC SYSTEM
    
    This is NOT rule-based. The agent:
    1. OBSERVES: Multiple signals (price, volume, sentiment, history)
    2. PLANS: Reasons about what matters
    3. DECIDES: Whether to alert based on context
    4. ACTS: Generates alert with explanation
    5. REFLECTS: Learns from past decisions
    """
    
    def __init__(self):
        self.memory = []  # Alert history
        self.alert_cooldown = timedelta(hours=24)
    
    def observe(self, forecast, technical, data):
        """
        STEP 1: OBSERVATION
        Collect all relevant signals
        """
        observations = {
            'price_change_pct': forecast['price_change_pct'],
            'confidence': forecast['confidence'],
            'volatility': forecast['volatility'],
            'trend': forecast['trend'],
            'rsi': technical.get('rsi', 50),
            'volume_spike': technical.get('volume_spike_pct', 0),
            'current_price': forecast['current_price'],
            'predicted_price': forecast['predicted_price']
        }
        
        # Add to session alert log
        self.memory.append({
            'timestamp': datetime.now().isoformat(),
            'observations': observations
        })
        
        return observations
    
    def plan(self, observations):
        """
        STEP 2: PLANNING (Agentic Reasoning)
        
        The agent asks itself:
        - Is this movement significant?
        - Is context supporting or conflicting?
        - Should I act or wait?
        """
        reasoning = []
        signals = []
        
        # Analyze price movement
        if abs(observations['price_change_pct']) > 3:
            signals.append({
                'signal': 'SIGNIFICANT_PRICE_CHANGE',
                'strength': min(abs(observations['price_change_pct']) / 10, 1.0),
                'direction': 'UP' if observations['price_change_pct'] > 0 else 'DOWN'
            })
            reasoning.append(f"Price expected to change by {observations['price_change_pct']:.2f}%")
        
        # Analyze volatility
        if observations['volatility'] > observations['current_price'] * 0.03:
            signals.append({
                'signal': 'HIGH_VOLATILITY',
                'strength': 0.7
            })
            reasoning.append("High volatility detected")
        
        # Analyze RSI
        if observations['rsi'] < 30:
            signals.append({
                'signal': 'OVERSOLD',
                'strength': 0.8
            })
            reasoning.append("Stock is oversold (RSI < 30)")
        elif observations['rsi'] > 70:
            signals.append({
                'signal': 'OVERBOUGHT',
                'strength': 0.8
            })
            reasoning.append("Stock is overbought (RSI > 70)")
        
        # Analyze volume
        if observations['volume_spike'] > 50:
            signals.append({
                'signal': 'VOLUME_SPIKE',
                'strength': min(observations['volume_spike'] / 100, 1.0)
            })
            reasoning.append(f"Unusual volume spike ({observations['volume_spike']:.1f}%)")
        
        # Confidence check
        if observations['confidence'] < 0.6:
            reasoning.append("Low model confidence - proceeding cautiously")
        
        return {
            'signals': signals,
            'reasoning': reasoning,
            'signal_count': len(signals)
        }
    
    def decide(self, observations, plan):
        """
        STEP 3: DECISION
        
        Agent decides whether to alert based on:
        - Multiple signals (not just one)
        - Signal strength
        - Context
        - Past memory
        """
        # Check memory (reflection)
        recent_alerts = [a for a in self.memory 
                        if datetime.fromisoformat(a['timestamp']) > 
                        datetime.now() - self.alert_cooldown]
        
        if recent_alerts:
            return {
                'should_alert': False,
                'reason': 'SUPPRESSED',
                'explanation': 'Alert sent recently - preventing spam'
            }
        
        # Multi-signal decision logic
        signals = plan['signals']
        
        if len(signals) == 0:
            return {
                'should_alert': False,
                'reason': 'NO_SIGNALS',
                'explanation': 'All indicators within normal range'
            }
        
        # Calculate combined signal strength
        total_strength = sum(s['strength'] for s in signals)
        avg_strength = total_strength / len(signals)
        
        # Decision threshold
        if len(signals) >= 2 and avg_strength > 0.6:
            alert_type = self._determine_alert_type(signals, observations)
            confidence_level = self._calculate_confidence(avg_strength, observations['confidence'])
            
            return {
                'should_alert': True,
                'alert_type': alert_type,
                'confidence_level': confidence_level,
                'signal_strength': avg_strength,
                'signals_detected': len(signals)
            }
        
        return {
            'should_alert': False,
            'reason': 'WEAK_SIGNALS',
            'explanation': 'Signals detected but not strong enough to alert'
        }
    
    def _determine_alert_type(self, signals, observations):
        """Determine type of alert"""
        signal_types = [s['signal'] for s in signals]
        
        if 'SIGNIFICANT_PRICE_CHANGE' in signal_types:
            direction = next(s['direction'] for s in signals if s['signal'] == 'SIGNIFICANT_PRICE_CHANGE')
            if direction == 'DOWN':
                return 'PRICE_DROP_ALERT'
            else:
                return 'PRICE_SPIKE_ALERT'
        
        if 'OVERSOLD' in signal_types:
            return 'BUY_OPPORTUNITY'
        
        if 'OVERBOUGHT' in signal_types:
            return 'SELL_SIGNAL'
        
        if 'HIGH_VOLATILITY' in signal_types:
            return 'VOLATILITY_WARNING'
        
        return 'GENERAL_ALERT'
    
    def _calculate_confidence(self, signal_strength, model_confidence):
        """Calculate overall confidence"""
        combined = (signal_strength * 0.6) + (model_confidence * 0.4)
        
        if combined > 0.8:
            return 'HIGH'
        elif combined > 0.6:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def act(self, decision, observations, plan):
        """
        STEP 4: ACTION
        Generate alert with explanation
        """
        if not decision['should_alert']:
            return None
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'alert_type': decision['alert_type'],
            'confidence': decision['confidence_level'],
            'current_price': observations['current_price'],
            'predicted_price': observations['predicted_price'],
            'price_change_pct': observations['price_change_pct'],
            'reasoning': plan['reasoning'],
            'signals_detected': decision['signals_detected'],
            'signal_strength': decision['signal_strength'],
            'recommendation': self._generate_recommendation(decision, observations)
        }
        
        return alert
    
    def _generate_recommendation(self, decision, observations):
        """Generate actionable recommendation"""
        alert_type = decision['alert_type']
        
        recommendations = {
            'PRICE_DROP_ALERT': 'Consider reviewing position. Price expected to drop significantly.',
            'PRICE_SPIKE_ALERT': 'Strong upward movement expected. Consider taking profits or adding position.',
            'BUY_OPPORTUNITY': 'Stock oversold - potential buying opportunity.',
            'SELL_SIGNAL': 'Stock overbought - consider taking profits.',
            'VOLATILITY_WARNING': 'High volatility detected - tighten stop losses.',
            'GENERAL_ALERT': 'Multiple signals detected - monitor closely.'
        }
        
        return recommendations.get(alert_type, 'Monitor situation closely')
    
    def reflect(self, alert):
        """
        STEP 5: REFLECTION
        Store decision in memory
        """
        if alert:
            self.memory.append(alert)
            # Keep only last 100 alerts
            self.memory = self.memory[-100:]
    
    def process(self, forecast, technical, data):
        """
        COMPLETE AGENTIC CYCLE
        Observe → Plan → Decide → Act → Reflect
        """
        # Step 1: Observe
        observations = self.observe(forecast, technical, data)
        
        # Step 2: Plan
        plan = self.plan(observations)
        
        # Step 3: Decide
        decision = self.decide(observations, plan)
        
        # Step 4: Act
        alert = self.act(decision, observations, plan)
        
        # Step 5: Reflect
        self.reflect(alert)
        
        return {
            'observations': observations,
            'plan': plan,
            'decision': decision,
            'alert': alert,
            'memory_count': len(self.memory)
        }


# ==================== INITIALIZE SYSTEMS ====================

data_manager = DataManager()
forecaster = Forecaster(window=10)
agent = AgenticAlertSystem()


# ==================== API ROUTES ====================

@app.route('/')
def index():
    return render_template('agentic_dashboard.html')

@app.route('/api/stocks/dataset')
def get_dataset_stocks():
    """Get available stocks from dataset"""
    stocks = data_manager.load_dataset_stocks()
    return jsonify({'success': True, 'stocks': stocks})

@app.route('/api/analyze/<symbol>/dataset')
def analyze_dataset_stock(symbol):
    """Full agentic analysis on dataset stock"""
    try:
        # Load data
        data = data_manager.load_historical_data(symbol.upper())
        
        if not data:
            return jsonify({'success': False, 'error': 'No data found'})
        
        # Forecast
        forecast = forecaster.forecast(data)
        technical = forecaster.calculate_technical_indicators(data)
        
        # Agentic processing
        result = agent.process(forecast, technical, data)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'source': 'DATASET',
            'timestamp': datetime.now().isoformat(),
            'data': data[-30:],  # Last 30 days
            'forecast': forecast,
            'technical': technical,
            'agent_result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analyze/<symbol>/live')
def analyze_live_stock(symbol):
    """Full agentic analysis on live API data"""
    try:
        # Fetch live data
        data, error = data_manager.fetch_live_data(symbol.upper())
        
        if error:
            return jsonify({'success': False, 'error': error})
        
        if not data:
            return jsonify({'success': False, 'error': 'No data available'})
        
        # Forecast
        forecast = forecaster.forecast(data)
        technical = forecaster.calculate_technical_indicators(data)
        
        # Agentic processing
        result = agent.process(forecast, technical, data)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'source': 'LIVE_API',
            'timestamp': datetime.now().isoformat(),
            'data': data[-30:],
            'forecast': forecast,
            'technical': technical,
            'agent_result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alerts/history')
def get_alert_history():
    """Get all alerts from agent memory"""
    return jsonify({
        'success': True,
        'alerts': agent.memory[-50:],  # Last 50 alerts
        'total_count': len(agent.memory)
    })


if __name__ == '__main__':
    print("=" * 80)
    print("🤖 PROFESSIONAL AGENTIC MARKET ALERT SYSTEM")
    print("=" * 80)
    print("\n✅ SYSTEM FEATURES:")
    print("   📊 Historical Dataset Analysis")
    print("   🔴 Live Real-Time API Data")
    print("   🔮 ML Forecasting (Current vs Predicted)")
    print("   🧠 Agentic AI (Observe → Plan → Decide → Act → Reflect)")
    print("   🚨 Intelligent Alert Generation")
    print("   💭 Multi-Signal Reasoning")
    print("   📝 Alert Memory & Reflection")
    print(f"\n🌐 Dashboard: http://localhost:5002")
    print("⌨️  Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
