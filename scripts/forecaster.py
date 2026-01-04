"""
Forecasting Module
==================
Time-series forecasting using ARIMA and Prophet models.
Predicts next-day closing prices and trend direction.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

warnings.filterwarnings('ignore', category=ConvergenceWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


class MarketForecaster:
    """
    Time-series forecaster for market data.
    Supports ARIMA and Prophet models.
    """
    
    def __init__(self, model_type: str = "arima"):
        """
        Initialize forecaster.
        
        Args:
            model_type: "arima" or "prophet"
        """
        self.model_type = model_type.lower()
        self.model = None
        self.fitted = False
        
    def fit(self, data: pd.DataFrame, target_col: str = "Close") -> None:
        """
        Fit the forecasting model to historical data.
        
        Args:
            data: DataFrame with Date and OHLCV columns
            target_col: Column to forecast (default: Close)
        """
        if self.model_type == "arima":
            self._fit_arima(data, target_col)
        elif self.model_type == "prophet":
            self._fit_prophet(data, target_col)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
            
        self.fitted = True
    
    def _fit_arima(self, data: pd.DataFrame, target_col: str) -> None:
        """Fit ARIMA model."""
        y = data[target_col].values
        
        # Use ARIMA(1,1,1) as default - good balance for most financial data
        self.model = ARIMA(y, order=(1, 1, 1))
        self.model_fit = self.model.fit()
        
    def _fit_prophet(self, data: pd.DataFrame, target_col: str) -> None:
        """Fit Prophet model."""
        try:
            from prophet import Prophet
        except ImportError:
            raise ImportError("Prophet not installed. Install with: pip install prophet")
        
        # Prepare data for Prophet
        df_prophet = pd.DataFrame({
            'ds': pd.to_datetime(data['Date']),
            'y': data[target_col]
        })
        
        self.model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=False,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05
        )
        self.model.fit(df_prophet)
    
    def forecast(self, steps: int = 1) -> Dict[str, float]:
        """
        Forecast future values.
        
        Args:
            steps: Number of steps ahead to forecast
            
        Returns:
            Dictionary with forecast results
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if self.model_type == "arima":
            return self._forecast_arima(steps)
        elif self.model_type == "prophet":
            return self._forecast_prophet(steps)
    
    def _forecast_arima(self, steps: int) -> Dict[str, float]:
        """Forecast with ARIMA."""
        forecast = self.model_fit.forecast(steps=steps)
        forecast_values = forecast if isinstance(forecast, np.ndarray) else [forecast]
        
        # Get confidence intervals
        forecast_result = self.model_fit.get_forecast(steps=steps)
        conf_int = forecast_result.conf_int()
        
        return {
            'predicted_value': float(forecast_values[0]),
            'lower_bound': float(conf_int.iloc[0, 0]),
            'upper_bound': float(conf_int.iloc[0, 1]),
            'confidence': 0.95
        }
    
    def _forecast_prophet(self, steps: int) -> Dict[str, float]:
        """Forecast with Prophet."""
        future = self.model.make_future_dataframe(periods=steps)
        forecast = self.model.predict(future)
        
        last_forecast = forecast.iloc[-1]
        
        return {
            'predicted_value': float(last_forecast['yhat']),
            'lower_bound': float(last_forecast['yhat_lower']),
            'upper_bound': float(last_forecast['yhat_upper']),
            'confidence': 0.95
        }
    
    def calculate_volatility(self, data: pd.DataFrame, window: int = 10) -> float:
        """
        Calculate rolling volatility (standard deviation of returns).
        
        Args:
            data: DataFrame with Close prices
            window: Rolling window size
            
        Returns:
            Recent volatility value
        """
        returns = data['Close'].pct_change()
        volatility = returns.rolling(window=window).std()
        return float(volatility.iloc[-1])
    
    def detect_trend(self, data: pd.DataFrame, window: int = 10) -> str:
        """
        Detect current trend direction.
        
        Args:
            data: DataFrame with Close prices
            window: Window for trend calculation
            
        Returns:
            "upward", "downward", or "stable"
        """
        recent_prices = data['Close'].tail(window)
        
        # Calculate linear regression slope
        x = np.arange(len(recent_prices))
        y = recent_prices.values
        slope = np.polyfit(x, y, 1)[0]
        
        # Determine trend
        if slope > 0.5:
            return "upward"
        elif slope < -0.5:
            return "downward"
        else:
            return "stable"
    
    def calculate_metrics(self, data: pd.DataFrame, forecast_result: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate additional metrics for decision making.
        
        Args:
            data: Historical data
            forecast_result: Forecast output
            
        Returns:
            Dictionary of metrics
        """
        last_close = data['Close'].iloc[-1]
        predicted = forecast_result['predicted_value']
        
        # Calculate percentage change
        pct_change = ((predicted - last_close) / last_close) * 100
        
        # Calculate volatility
        volatility = self.calculate_volatility(data)
        
        # Detect trend
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
    """
    Load market data from CSV file.
    
    Args:
        file_path: Path to CSV file with OHLCV data
        
    Returns:
        DataFrame with parsed dates
    """
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df


if __name__ == "__main__":
    # Example usage
    print("=== Market Forecaster Demo ===\n")
    
    # Load sample data
    data = load_market_data("../data/sample_stock_data.csv")
    print(f"Loaded {len(data)} days of market data")
    print(f"Date range: {data['Date'].min()} to {data['Date'].max()}\n")
    
    # Initialize and fit forecaster
    forecaster = MarketForecaster(model_type="arima")
    forecaster.fit(data, target_col="Close")
    print("✓ Model fitted\n")
    
    # Make forecast
    forecast = forecaster.forecast(steps=1)
    print("Forecast Results:")
    print(f"  Predicted Close: ${forecast['predicted_value']:.2f}")
    print(f"  Range: ${forecast['lower_bound']:.2f} - ${forecast['upper_bound']:.2f}")
    print(f"  Confidence: {forecast['confidence']*100:.0f}%\n")
    
    # Calculate metrics
    metrics = forecaster.calculate_metrics(data, forecast)
    print("Analysis Metrics:")
    print(f"  Last Close: ${metrics['last_close']:.2f}")
    print(f"  Predicted Change: {metrics['percent_change']:+.2f}%")
    print(f"  Volatility: {metrics['volatility']:.4f}")
    print(f"  Trend: {metrics['trend']}")
