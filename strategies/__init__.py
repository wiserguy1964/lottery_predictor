"""
Prediction strategies

All strategies inherit from BaseStrategy and implement:
    - predict(draws, start_idx, end_idx) -> Prediction
    - calculate_confidence(draws, start_idx, end_idx) -> float

Available Strategies:
    - STRAT01: State Patterns + Frequency (Original Algorithm)
    - STRAT02: Pure Frequency Based
    - STRAT03: State Patterns + Random
    - STRAT04: Avoid Recent Numbers
    - STRAT05: Markov Chain Prediction
    - STRAT07: Adaptive Ensemble Strategy

Usage:
    from strategies import Strategy01_StatePatternFreq, get_all_strategies
    
    # Single strategy
    strategy = Strategy01_StatePatternFreq(lottery_config)
    prediction = strategy.predict(draws, start_idx, end_idx)
    
    # All strategies at once
    all_strategies = get_all_strategies(lottery_config)
"""

from .base_strategy import BaseStrategy
from .strat01_state_frequency import Strategy01_StatePatternFreq
from .strat02_pure_frequency import Strategy02_PureFrequency
from .strat03_state_random import Strategy03_StatePatternRandom
from .strat04_avoid_recent import Strategy04_AvoidRecent
from .strat05_markov_chain import Strategy05_MarkovChain
from .strat07_ensemble import Strategy07_AdaptiveEnsemble

__all__ = [
    'BaseStrategy',
    'Strategy01_StatePatternFreq',
    'Strategy02_PureFrequency',
    'Strategy03_StatePatternRandom',
    'Strategy04_AvoidRecent',
    'Strategy05_MarkovChain',
    'Strategy07_AdaptiveEnsemble'
]

__version__ = '1.0.0'


# Strategy registry for easy access
STRATEGY_MAP = {
    'STRAT01': Strategy01_StatePatternFreq,
    'STRAT02': Strategy02_PureFrequency,
    'STRAT03': Strategy03_StatePatternRandom,
    'STRAT04': Strategy04_AvoidRecent,
    'STRAT05': Strategy05_MarkovChain,
    'STRAT07': Strategy07_AdaptiveEnsemble,
}


def get_strategy(strategy_id: str, lottery_config):
    """
    Get strategy instance by ID
    
    Args:
        strategy_id: Strategy ID (e.g., 'STRAT01')
        lottery_config: LotteryConfig instance
        
    Returns:
        Strategy instance
        
    Raises:
        KeyError: If strategy_id not found
    """
    if strategy_id not in STRATEGY_MAP:
        available = list(STRATEGY_MAP.keys())
        raise KeyError(
            f"Strategy '{strategy_id}' not found.\n"
            f"Available strategies: {available}"
        )
    
    strategy_class = STRATEGY_MAP[strategy_id]
    return strategy_class(lottery_config)


def get_all_strategies(lottery_config, include_ensemble=True):
    """
    Get all strategy instances
    
    Args:
        lottery_config: LotteryConfig instance
        include_ensemble: Whether to include ensemble strategy
        
    Returns:
        List of strategy instances
    """
    strategies = []
    
    for strategy_id in ['STRAT01', 'STRAT02', 'STRAT03', 'STRAT04', 'STRAT05']:
        strategies.append(get_strategy(strategy_id, lottery_config))
    
    if include_ensemble:
        # Create ensemble with base strategies
        ensemble = Strategy07_AdaptiveEnsemble(lottery_config, strategies.copy())
        strategies.append(ensemble)
    
    return strategies


# Add to __all__
__all__.extend(['STRATEGY_MAP', 'get_strategy', 'get_all_strategies'])
