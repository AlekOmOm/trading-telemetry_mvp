""" using numpy and pandas for basic analysis of real trades (not benchmarking) """

import numpy as np
import pandas as pd
from typing import Dict, List
from collections import deque


class TradeAnalyzer:
    """Simple trade analysis using NumPy and Pandas for exam demonstration."""
    
    def __init__(self, max_trades: int = 100):
        self.trades = deque(maxlen=max_trades)
        
    def add_trade(self, side: str, qty: float, timestamp: float) -> None:
        """Add trade for analysis."""
        self.trades.append({'side': side, 'qty': qty, 'ts': timestamp})
    
    def get_numpy_stats(self) -> Dict[str, float]:
        """Basic NumPy operations on trade quantities."""
        if not self.trades:
            return {'mean_qty': 0.0, 'std_qty': 0.0, 'max_qty': 0.0}
            
        # np array conversion
        quantities = np.array([t['qty'] for t in self.trades])
        
        return {
            'mean_qty': float(np.mean(quantities)),
            'std_qty': float(np.std(quantities)),
            'max_qty': float(np.max(quantities))
        }
    
    def get_pandas_analysis(self) -> Dict[str, float]:
        """Basic Pandas operations on trade data."""
        if not self.trades:
            return {'buy_count': 0, 'sell_count': 0, 'buy_volume': 0.0}
            
        df = pd.DataFrame(self.trades)
        
        buy_trades = df[df['side'] == 'buy']
        sell_trades = df[df['side'] == 'sell']
        
        return {
            'buy_count': float(len(buy_trades)),
            'sell_count': float(len(sell_trades)),
            'buy_volume': float(buy_trades['qty'].sum()) if len(buy_trades) > 0 else 0.0
        }
