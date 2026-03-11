"""
Strategy 05: Markov Chain Prediction
Position-based Markov chain transitions
"""
from typing import List
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from analyzers.state_machine import MarkovChainPredictor
from analyzers.frequency_analyzer import FrequencyAnalyzer
from config import LotteryConfig


class Strategy05_MarkovChain(BaseStrategy):
    """
    Markov Chain Strategy
    
    Uses position-based Markov chain transitions to predict next numbers.
    Combines Markov predictions (40%) with frequency analysis (60%).
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT05", "Markov Chain Prediction")
        self.markov = MarkovChainPredictor(lottery_config)
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using Markov chains"""
        
        # 1. Build Markov chains
        self.markov.build_from_draws(draws, start_idx, end_idx)
        
        # 2. Get Markov predictions for each position
        markov_predictions = self.markov.predict_numbers(draws[end_idx])
        
        # 3. Get frequency-based predictions
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 4. Combine Markov and frequency with weighted probabilities
        probabilities = np.zeros(self.config.main_pool + 1)
        
        # Add Markov component (40%)
        for num in markov_predictions:
            if 1 <= num <= self.config.main_pool:
                probabilities[num] += 0.4
        
        # Add frequency component (60%)
        max_freq = np.max(frequencies[1:]) if np.max(frequencies[1:]) > 0 else 1
        for i in range(1, self.config.main_pool + 1):
            probabilities[i] += (frequencies[i] / max_freq) * 0.6
        
        # 5. Select top numbers by combined probability
        number_prob_pairs = [(num, prob) for num, prob in enumerate(probabilities[1:], start=1)]
        number_prob_pairs.sort(key=lambda x: -x[1])
        
        main_numbers = [num for num, prob in number_prob_pairs[:self.config.main_play_count]]
        main_numbers.sort()
        
        # 6. Get current patterns (no pattern prediction in this strategy)
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        current_sum_bracket = current_draw.get_sum_bracket()
        
        # 7. Predict bonus
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 8. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx)
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=current_oe,
            predicted_hl=current_hl,
            predicted_sum_bracket=current_sum_bracket,
            confidence_score=confidence,
            metadata={
                'markov_predictions': markov_predictions,
                'markov_weight': 0.4,
                'frequency_weight': 0.6
            }
        )
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> float:
        """
        Confidence based on transition data availability
        
        Higher confidence when we have more historical transitions.
        """
        window_size = end_idx - start_idx + 1
        
        # More data = higher confidence (up to a point)
        if window_size < 30:
            base_confidence = 0.3
        elif window_size < 60:
            base_confidence = 0.5
        elif window_size < 90:
            base_confidence = 0.7
        else:
            base_confidence = 0.75
        
        return base_confidence