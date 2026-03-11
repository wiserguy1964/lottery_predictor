"""
Analysis components for frequency, patterns, and state machines

Components:
    - FrequencyAnalyzer: Analyzes number frequencies and hot/cold numbers
    - PatternAnalyzer: Analyzes pattern frequencies and streaks
    - StateMachine: Markov-like state transitions for pattern prediction
    - MarkovChainPredictor: Position-based Markov chain for number prediction

Usage:
    from analyzers import FrequencyAnalyzer, StateMachine
    
    freq_analyzer = FrequencyAnalyzer(lottery_config)
    hot_numbers = freq_analyzer.get_hot_numbers(draws, count=12)
    
    state_machine = StateMachine(lottery_config)
    state_machine.build_from_draws(draws, start_idx, end_idx)
    predicted_oe = state_machine.predict_next_pattern(current_oe, 'OE')
"""

from .frequency_analyzer import FrequencyAnalyzer, PatternAnalyzer
from .state_machine import StateMachine, MarkovChainPredictor

__all__ = [
    'FrequencyAnalyzer',
    'PatternAnalyzer',
    'StateMachine',
    'MarkovChainPredictor'
]

__version__ = '1.0.0'
