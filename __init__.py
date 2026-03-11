"""
Lottery Prediction System

A sophisticated parameter-driven system for analyzing and predicting lottery draws
with multiple strategies and dynamic ensemble weighting.

Project Home: C:\DEV_AREA\lottery_predictor

Usage:
    from lottery_predictor import get_lottery_config, Strategy01_StatePatternFreq
    
    config = get_lottery_config('OPAP_JOKER')
    strategy = Strategy01_StatePatternFreq(config)

Main Components:
    - config: Configuration loader
    - core: Data fetching and loading
    - models: Draw and Prediction data models
    - analyzers: Frequency, pattern, and state machine analysis
    - strategies: All prediction strategies
    - predictors: Joker/bonus number prediction
    - backtesting: Rolling window backtest engine
    - visualization: Excel export and reporting
"""

__version__ = '1.0.0'
__author__ = 'Converted from VBA'

# Import key components for easy access
from .config import (
    get_lottery_config,
    get_backtest_config,
    get_config_loader,
    LotteryConfig,
    BacktestConfig
)

from .models import Draw, Prediction

# Import all strategies
from .strategies import (
    BaseStrategy,
    Strategy01_StatePatternFreq,
    Strategy02_PureFrequency,
    Strategy03_StatePatternRandom,
    Strategy04_AvoidRecent,
    Strategy05_MarkovChain,
    Strategy07_AdaptiveEnsemble
)

# Import predictors
from .predictors import JokerPredictor

# Import backtesting
from .backtesting import RollingWindowBacktester

# Import visualization
from .visualization import ExcelExporter

# Import core data handling
from .core import OPAPDataFetcher, DrawDataLoader

__all__ = [
    # Version
    '__version__',
    
    # Configuration
    'get_lottery_config',
    'get_backtest_config',
    'get_config_loader',
    'LotteryConfig',
    'BacktestConfig',
    
    # Models
    'Draw',
    'Prediction',
    
    # Strategies
    'BaseStrategy',
    'Strategy01_StatePatternFreq',
    'Strategy02_PureFrequency',
    'Strategy03_StatePatternRandom',
    'Strategy04_AvoidRecent',
    'Strategy05_MarkovChain',
    'Strategy07_AdaptiveEnsemble',
    
    # Predictors
    'JokerPredictor',
    
    # Backtesting
    'RollingWindowBacktester',
    
    # Visualization
    'ExcelExporter',
    
    # Data handling
    'OPAPDataFetcher',
    'DrawDataLoader',
]


# Convenience function for quick setup
def quick_start(lottery_name='OPAP_JOKER', fetch_data=False):
    """
    Quick start helper function
    
    Args:
        lottery_name: Name of lottery (default: OPAP_JOKER)
        fetch_data: Whether to fetch fresh data (default: False)
        
    Returns:
        Tuple of (lottery_config, backtest_config, draws)
        
    Example:
        >>> from lottery_predictor import quick_start
        >>> config, backtest, draws = quick_start('OPAP_JOKER')
        >>> print(f"Loaded {len(draws)} draws")
    """
    lottery_config = get_lottery_config(lottery_name)
    backtest_config = get_backtest_config()
    
    fetcher = OPAPDataFetcher(lottery_config)
    loader = DrawDataLoader(lottery_name)
    draws = loader.get_or_fetch_draws(fetcher, force_refresh=fetch_data)
    
    return lottery_config, backtest_config, draws


# Add to __all__
__all__.append('quick_start')
