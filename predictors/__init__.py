"""
Bonus/Joker number predictors

Components:
    - JokerPredictor: Independent bonus number prediction with 4 methods
      - Frequency method
      - Avoid recent method
      - Markov method
      - Random method
      - Dynamic weighted combination

Usage:
    from predictors import JokerPredictor
    
    predictor = JokerPredictor(lottery_config)
    joker = predictor.predict_dynamic(draws, start_idx, end_idx)
    print(f"Predicted Joker: {joker}")
"""

from .joker_predictor import JokerPredictor

__all__ = ['JokerPredictor']

__version__ = '1.0.0'
