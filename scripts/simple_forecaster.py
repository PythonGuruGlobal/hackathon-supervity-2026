"""
Simple Forecasting Module (No statsmodels dependency)
Uses moving averages and simple linear regression for forecasting
"""

import pandas as pd
import numpy as np
from typing import Dict


class SimpleForecaster:
    """Simple forecaster using moving averages and linear trends."""
    
    def __init__(self, window: int = 10):
        self.window = window
        self.data = None
        self.fitted = False
        
    def fit(self, data: pd.DataFrame, target_col: str = "Close") -> None:
        """Fit the forecaster to data."""
        self.data = data.copy()
        self.target_col = target_col
        self.fitted = True
        
    def forecast(self, steps: int = 1) -> Dict[str, float]:
        """Simple forecast using moving average and trend."""
        if not self.fitted:
            raise ValueError("Model not fitted")
        
        prices = self.data[self.target_col].values
        
        # Calculate moving average
        ma = np.mean(prices[-self.window:])
        
        # Calculate trend (simple linear regression on recent data)
        recent = prices[-self.window:]
        x = np.arange(len(recent))
        coeffs = np.polyfit(x, recent, 1)
        trend = coeffs[0]  # slope
        
        # Forecast = MA + trend projection
        forecast_value = ma + (trend * steps)
        
        # Estimate confidence interval based on recent volatility
        std = np.std(prices[-self.window:])
        lower = forecast_value - (1.96 * std)
        upper = forecast_value + (1.96 * std)
        
        return {
            'predicted_value': float(forecast_value),
            'lower_bound': float(lower),
            'upper_bound': float(upper),
            'confidence': 0.95
        }
    
    def calculate_volatility(self, data: pd.DataFrame, window: int = 10) -> float:
        """Calculate rolling volatility."""
        returns = data['Close'].pct_change()
        volatility = returns.rolling(window=window).std()
        return float(volatility.iloc[-1]) if not volatility.empty else 0.0
    
    def detect_trend(self, data: pd.DataFrame, window: int = 10) -> str:
        """Detect trend direction."""
        recent_prices = data['Close'].tail(window)
        
        x = np.arange(len(recent_prices))
        y = recent_prices.values
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.5:
            return "upward"
        elif slope < -0.5:
            return "downward"
        else:
            return "stable"
    
    def calculate_metrics(self, data: pd.DataFrame, forecast_result: Dict[str, float]) -> Dict[str, float]:
        """Calculate metrics for decision making."""
        last_close = data['Close'].iloc[-1]
        predicted = forecast_result['predicted_value']
        
        pct_change = ((predicted - last_close) / last_close) * 100
        volatility = self.calculate_volatility(data)
        trend = self.detect_trend(data)
        
        return {
            'last_close': float(last_close),
            'predicted_close': float(predicted),
            'percent_change': float(pct_change),
            'volatility': float(volatility),
            'trend': trend,
            'prediction_range': float(forecast_result['upper_bound'] - forecast_result['lower_bound'])
        }


def load_market_data(file_path: str) -> pd.DataFrame:
    """Load market data from CSV."""
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=== Simple Forecaster Demo ===\n")
    
    data = load_market_data("../data/aapl_recent.csv")
    print(f"Loaded {len(data)} days")
    
    forecaster = SimpleForecaster(window=10)
    forecaster.fit(data)
    
    forecast = forecaster.forecast(steps=1)
    print(f"\nForecast: ${forecast['predicted_value']:.2f}")
    print(f"Range: ${forecast['lower_bound']:.2f} - ${forecast['upper_bound']:.2f}")
    
    metrics = forecaster.calculate_metrics(data, forecast)
    print(f"\nMetrics:")
    print(f"  Last: ${metrics['last_close']:.2f}")
    print(f"  Change: {metrics['percent_change']:+.2f}%")
    print(f"  Volatility: {metrics['volatility']:.4f}")
    print(f"  Trend: {metrics['trend']}")
