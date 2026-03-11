"""
Backtesting framework

Components:
    - RollingWindowBacktester: Multi-strategy rolling window backtesting

Usage:
    from backtesting import RollingWindowBacktester
    from strategies import Strategy01_StatePatternFreq
    
    backtester = RollingWindowBacktester(lottery_config, backtest_config)
    backtester.add_strategy(Strategy01_StatePatternFreq(lottery_config))
    
    results = backtester.run_backtest(draws)
    summaries = backtester.calculate_summary_metrics(results)
    rankings = backtester.rank_strategies(summaries)
"""

from .rolling_window import RollingWindowBacktester

__all__ = ['RollingWindowBacktester']

__version__ = '1.0.0'
