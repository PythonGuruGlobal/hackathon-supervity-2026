"""
Enhanced Agentic System with Authentication & Investment Tracking
==================================================================
Adds user authentication, portfolio management, and personalized alerts.
"""

from flask import Flask, render_template, jsonify, request
from database import Database
from auth import JWTAuth, token_required, optional_token
import requests
from datetime import datetime
import json

app = Flask(__name__)
db = Database()

# ==================== API CONFIGURATION ====================
API_KEY = "BEWGGWDHQV07D4GG"
BASE_URL = "https://www.alphavantage.co/query"


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration endpoint."""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        phone = data.get('phone')
        
        if not all([username, email, password]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Create user
        user_id = db.create_user(username, email, password, full_name, phone)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Username or email already exists'
            }), 409
        
        # Generate token
        token = JWTAuth.generate_token(user_id, username, email)
        db.save_token(user_id, token)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({
                'success': False,
                'error': 'Missing username or password'
            }), 400
        
        # Authenticate user
        user = db.authenticate_user(username, password)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
        
        # Generate token
        token = JWTAuth.generate_token(user['id'], user['username'], user['email'])
        db.save_token(user['id'], token)
        
        # Get portfolio info
        portfolio = db.get_user_portfolio(user['id'])
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'phone': user['phone'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            },
            'portfolio': portfolio
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Logout endpoint - revokes token."""
    try:
        token = JWTAuth.get_token_from_header()
        db.revoke_token(token)
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user info."""
    try:
        user = db.get_user_by_id(current_user['user_id'])
        portfolio = db.get_user_portfolio(current_user['user_id'])
        
        return jsonify({
            'success': True,
            'user': user,
            'portfolio': portfolio
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== PORTFOLIO & INVESTMENT ROUTES ====================

@app.route('/api/portfolio', methods=['GET'])
@token_required
def get_portfolio(current_user):
    """Get user's portfolio details."""
    try:
        portfolio = db.get_user_portfolio(current_user['user_id'])
        investments = db.get_user_investments(current_user['user_id'])
        
        # Calculate total portfolio value
        total_value = portfolio['available_cash']
        for inv in investments:
            total_value += (inv['quantity'] * (inv['current_price'] or inv['buy_price']))
        
        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'investments': investments,
            'total_value': total_value,
            'investment_count': len(investments)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/investments', methods=['GET'])
@token_required
def get_investments(current_user):
    """Get user's investments."""
    try:
        status = request.args.get('status', 'active')
        investments = db.get_user_investments(current_user['user_id'], status)
        
        return jsonify({
            'success': True,
            'investments': investments,
            'count': len(investments)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/investments/create', methods=['POST'])
@token_required
def create_investment(current_user):
    """Create new investment."""
    try:
        data = request.json
        stock_symbol = data.get('stock_symbol')
        quantity = float(data.get('quantity', 0))
        buy_price = float(data.get('buy_price', 0))
        notes = data.get('notes')
        
        if not all([stock_symbol, quantity > 0, buy_price > 0]):
            return jsonify({
                'success': False,
                'error': 'Invalid investment data'
            }), 400
        
        portfolio = db.get_user_portfolio(current_user['user_id'])
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found'
            }), 404
        
        # Check if user needs to confirm
        alert_settings = db.get_alert_settings(current_user['user_id'])
        total_cost = quantity * buy_price
        
        if alert_settings and alert_settings.get('require_confirmation'):
            # Create alert for user to confirm
            alert_id = db.create_alert(
                user_id=current_user['user_id'],
                stock_symbol=stock_symbol,
                alert_type='investment_confirmation',
                alert_message=f'Confirm investment: Buy {quantity} shares of {stock_symbol} at ${buy_price:.2f} (Total: ${total_cost:.2f})',
                severity='high',
                metadata={
                    'stock_symbol': stock_symbol,
                    'quantity': quantity,
                    'buy_price': buy_price,
                    'total_cost': total_cost
                }
            )
            
            return jsonify({
                'success': True,
                'requires_confirmation': True,
                'alert_id': alert_id,
                'message': 'Investment pending confirmation'
            }), 202
        
        # Create investment directly
        investment_id = db.create_investment(
            user_id=current_user['user_id'],
            portfolio_id=portfolio['id'],
            stock_symbol=stock_symbol,
            quantity=quantity,
            buy_price=buy_price,
            notes=notes
        )
        
        if not investment_id:
            return jsonify({
                'success': False,
                'error': 'Insufficient funds or invalid investment'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Investment created successfully',
            'investment_id': investment_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    """Get user's transaction history."""
    try:
        limit = int(request.args.get('limit', 100))
        transactions = db.get_transactions(current_user['user_id'], limit)
        
        return jsonify({
            'success': True,
            'transactions': transactions,
            'count': len(transactions)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ALERT ROUTES ====================

@app.route('/api/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    """Get user's alerts."""
    try:
        status = request.args.get('status', 'pending')
        limit = int(request.args.get('limit', 50))
        
        alerts = db.get_user_alerts(current_user['user_id'], status, limit)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts),
            'pending_count': len([a for a in alerts if a['status'] == 'pending'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@token_required
def acknowledge_alert(current_user, alert_id):
    """Acknowledge an alert."""
    try:
        data = request.json
        response = data.get('response', 'acknowledged')
        
        success = db.acknowledge_alert(alert_id, response)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Alert not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Alert acknowledged'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts/confirm-investment/<int:alert_id>', methods=['POST'])
@token_required
def confirm_investment_from_alert(current_user, alert_id):
    """Confirm investment from alert."""
    try:
        # Get alert details
        alerts = db.get_user_alerts(current_user['user_id'], None, 1000)
        alert = next((a for a in alerts if a['id'] == alert_id), None)
        
        if not alert or alert['alert_type'] != 'investment_confirmation':
            return jsonify({
                'success': False,
                'error': 'Invalid alert'
            }), 404
        
        # Parse metadata
        metadata = json.loads(alert['metadata']) if alert['metadata'] else {}
        
        # Create investment
        portfolio = db.get_user_portfolio(current_user['user_id'])
        investment_id = db.create_investment(
            user_id=current_user['user_id'],
            portfolio_id=portfolio['id'],
            stock_symbol=metadata['stock_symbol'],
            quantity=metadata['quantity'],
            buy_price=metadata['buy_price']
        )
        
        if not investment_id:
            return jsonify({
                'success': False,
                'error': 'Investment creation failed'
            }), 400
        
        # Acknowledge alert
        db.acknowledge_alert(alert_id, 'confirmed')
        
        return jsonify({
            'success': True,
            'message': 'Investment confirmed and created',
            'investment_id': investment_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts/settings', methods=['GET', 'PUT'])
@token_required
def alert_settings(current_user):
    """Get or update alert settings."""
    try:
        if request.method == 'GET':
            settings = db.get_alert_settings(current_user['user_id'])
            return jsonify({
                'success': True,
                'settings': settings
            }), 200
        
        elif request.method == 'PUT':
            data = request.json
            success = db.update_alert_settings(current_user['user_id'], **data)
            
            return jsonify({
                'success': success,
                'message': 'Settings updated' if success else 'Update failed'
            }), 200 if success else 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== MARKET DATA ROUTES (Protected) ====================

@app.route('/api/stocks/dataset', methods=['GET'])
@optional_token
def get_dataset_stocks(current_user):
    """Get available stocks from dataset."""
    from agentic_system import DataManager
    stocks = DataManager.load_dataset_stocks()
    
    return jsonify({
        'success': True,
        'stocks': stocks,
        'count': len(stocks),
        'user_authenticated': current_user is not None
    })


@app.route('/api/analyze/<stock>/<source>', methods=['POST'])
@token_required
def analyze_stock_protected(current_user, stock, source):
    """Analyze stock with personalized alert settings."""
    try:
        # Get user's alert settings
        alert_settings = db.get_alert_settings(current_user['user_id'], stock)
        
        # Import analysis functions
        from agentic_system import AgenticDecisionEngine
        
        # Perform analysis with user settings
        engine = AgenticDecisionEngine()
        
        if source == 'dataset':
            from agentic_system import DataManager
            data = DataManager.load_historical_data(stock)
        else:
            from agentic_system import DataManager
            data, error = DataManager.fetch_live_data(stock)
            if error:
                return jsonify({'success': False, 'error': error}), 400
        
        if not data:
            return jsonify({'success': False, 'error': 'No data available'}), 404
        
        # Make decision
        decision = engine.decide(data, stock)
        
        # Check if alert should be created
        if decision['should_alert'] and alert_settings:
            require_conf = alert_settings.get('require_confirmation', True)
            
            if require_conf:
                # Create alert for user
                alert_id = db.create_alert(
                    user_id=current_user['user_id'],
                    stock_symbol=stock,
                    alert_type=decision['decision'],
                    alert_message=decision['reasoning'],
                    severity=decision['severity'],
                    metadata=decision
                )
                
                decision['alert_id'] = alert_id
                decision['requires_acknowledgment'] = True
        
        return jsonify({
            'success': True,
            'stock': stock,
            'decision': decision,
            'user_settings': alert_settings
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    """Main dashboard (now with auth)."""
    return render_template('auth_dashboard.html')


@app.route('/login')
def login_page():
    """Login page."""
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    """Signup page."""
    return render_template('signup.html')


if __name__ == '__main__':
    print("="*80)
    print("🔐 AUTHENTICATED AGENTIC MARKET ALERT SYSTEM")
    print("="*80)
    print("\n✅ SYSTEM FEATURES:")
    print("   🔐 JWT Authentication")
    print("   👤 User Management")
    print("   💰 Portfolio Tracking")
    print("   📈 Investment Management")
    print("   🚨 Personalized Alerts")
    print("   ✅ Confirmation Required")
    print("   📊 Transaction History")
    print("\n🌐 Dashboard: http://localhost:5003")
    print("⌨️  Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
