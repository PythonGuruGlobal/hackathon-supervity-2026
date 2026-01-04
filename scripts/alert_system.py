"""
Alert System
============
Manages alert output to CSV, JSON, and console.
Production-ready structured output.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd


class AlertSystem:
    """
    Alert output management system.
    Handles writing alerts to multiple formats.
    """
    
    def __init__(self, output_dir: str = "../outputs"):
        """
        Initialize alert system.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.csv_path = self.output_dir / "alerts.csv"
        self.json_path = self.output_dir / "alerts.json"
        
        # Initialize CSV if not exists
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV with headers if it doesn't exist."""
        if not self.csv_path.exists():
            headers = [
                'timestamp',
                'date',
                'stock',
                'alert_triggered',
                'alert_type',
                'confidence',
                'last_close',
                'predicted_close',
                'percent_change',
                'volatility',
                'trend',
                'technical_reason',
                'human_explanation',
                'suppressed',
                'suppression_reason'
            ]
            
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    def log_alert(
        self,
        alert_data: Dict,
        stock_symbol: str = "SAMPLE",
        date: str = None
    ):
        """
        Log an alert to all output formats.
        
        Args:
            alert_data: Dictionary with alert information
            stock_symbol: Stock ticker symbol
            date: Date of the alert (defaults to today)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare record
        record = {
            'timestamp': timestamp,
            'date': date,
            'stock': stock_symbol,
            'alert_triggered': alert_data.get('alert_triggered', False),
            'alert_type': alert_data.get('alert_type'),
            'confidence': alert_data.get('confidence'),
            'last_close': alert_data.get('metrics', {}).get('last_close'),
            'predicted_close': alert_data.get('metrics', {}).get('predicted_close'),
            'percent_change': alert_data.get('metrics', {}).get('percent_change'),
            'volatility': alert_data.get('metrics', {}).get('volatility'),
            'trend': alert_data.get('metrics', {}).get('trend'),
            'technical_reason': alert_data.get('technical_reason'),
            'human_explanation': alert_data.get('human_explanation'),
            'suppressed': alert_data.get('suppressed', False),
            'suppression_reason': alert_data.get('suppression_reason')
        }
        
        # Write to CSV
        self._write_csv(record)
        
        # Write to JSON
        self._write_json(record)
        
        # Console output
        self._print_alert(record)
    
    def _write_csv(self, record: Dict):
        """Append record to CSV file."""
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=record.keys())
            writer.writerow(record)
    
    def _write_json(self, record: Dict):
        """Append record to JSON file (as JSON Lines)."""
        with open(self.json_path, 'a') as f:
            json.dump(record, f)
            f.write('\n')
    
    def _print_alert(self, record: Dict):
        """Print alert to console in readable format."""
        print(f"\n{'='*70}")
        print(f"[{record['timestamp']}] MARKET ALERT")
        print(f"{'='*70}")
        
        if record['alert_triggered']:
            print(f"⚠️  ALERT TRIGGERED")
            print(f"   Type: {record['alert_type']}")
            print(f"   Confidence: {record['confidence'].upper()}")
            print()
            print(f"📊 Market Data:")
            print(f"   Last Close: ${record['last_close']:.2f}")
            print(f"   Predicted: ${record['predicted_close']:.2f}")
            print(f"   Change: {record['percent_change']:+.2f}%")
            print(f"   Volatility: {record['volatility']:.4f}")
            print(f"   Trend: {record['trend']}")
            print()
            print(f"📝 Explanation:")
            print(f"   {record['human_explanation']}")
            print()
            
            if record['suppressed']:
                print(f"🚫 Alert Suppressed: {record['suppression_reason']}")
        else:
            print(f"✅ No Alert - Market Stable")
            print(f"   Price: ${record['last_close']:.2f} → ${record['predicted_close']:.2f}")
            print(f"   Change: {record['percent_change']:+.2f}%")
        
        print(f"{'='*70}\n")
    
    def get_alert_history(self, days: int = 7) -> pd.DataFrame:
        """
        Get recent alert history.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            DataFrame with alert history
        """
        if not self.csv_path.exists():
            return pd.DataFrame()
        
        df = pd.read_csv(self.csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter to recent days
        cutoff = datetime.now() - pd.Timedelta(days=days)
        df = df[df['timestamp'] >= cutoff]
        
        return df
    
    def generate_summary_report(self) -> str:
        """Generate a text summary of alert history."""
        df = self.get_alert_history(days=30)
        
        if df.empty:
            return "No alerts in the last 30 days."
        
        total_alerts = len(df)
        triggered_alerts = df['alert_triggered'].sum()
        suppressed_alerts = df['suppressed'].sum()
        
        alert_types = df[df['alert_triggered']]['alert_type'].value_counts()
        
        report = f"""
Alert Summary Report (Last 30 Days)
{'='*50}

Total Evaluations: {total_alerts}
Alerts Triggered: {triggered_alerts}
Alerts Suppressed: {suppressed_alerts}
Alert Rate: {(triggered_alerts/total_alerts*100):.1f}%

Alert Type Breakdown:
{alert_types.to_string() if not alert_types.empty else '  None'}

Recent Alerts:
"""
        
        recent = df[df['alert_triggered']].tail(5)
        for _, row in recent.iterrows():
            report += f"\n  [{row['date']}] {row['alert_type']} - {row['confidence']}"
        
        return report


if __name__ == "__main__":
    # Example usage
    print("=== Alert System Demo ===\n")
    
    # Initialize system
    alert_system = AlertSystem(output_dir="../outputs")
    
    # Example alert
    alert_data = {
        'alert_triggered': True,
        'alert_type': 'price_drop',
        'confidence': 'medium',
        'technical_reason': 'Predicted drop of 4.5%',
        'human_explanation': 'The forecast indicates a sharp 4.5% drop following increased volatility.',
        'suppressed': False,
        'metrics': {
            'last_close': 155.0,
            'predicted_close': 148.0,
            'percent_change': -4.5,
            'volatility': 0.025,
            'trend': 'downward'
        }
    }
    
    # Log alert
    alert_system.log_alert(alert_data, stock_symbol="AAPL", date="2024-01-10")
    
    print("\n✓ Alert logged to:")
    print(f"  - {alert_system.csv_path}")
    print(f"  - {alert_system.json_path}")
