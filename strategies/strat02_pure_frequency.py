"""
Strategy 02: Pure Frequency Based
Simple frequency analysis without pattern considerations
"""
from typing import List
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from analyzers.frequency_analyzer import FrequencyAnalyzer
from config import LotteryConfig


class Strategy02_PureFrequency(BaseStrategy):
    """
    Pure Frequency Strategy
    
    Selects the hottest numbers from the current window without
    considering pattern constraints.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT02", "Pure Frequency Based")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using pure frequency"""
        
        # 1. Get frequencies
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 2. Select top N hottest numbers
        hot_numbers = self.freq_analyzer.get_hot_numbers(
            draws,
            count=self.config.main_play_count,
            start_idx=start_idx,
            end_idx=end_idx
        )
        
        # 3. Get current patterns (no prediction, just current state)
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        current_sum_bracket = current_draw.get_sum_bracket()
        
        # 4. Predict bonus numbers (placeholder)
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 5. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx)
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(hot_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=current_oe,  # Just use current, no prediction
            predicted_hl=current_hl,  # Just use current, no prediction
            predicted_sum_bracket=current_sum_bracket,  # Just use current
            confidence_score=confidence,
            metadata={
                'note': 'Returns current patterns, does not predict'
            }
        )
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> float:
        """
        Calculate confidence based on frequency concentration
        
        Higher confidence when frequencies are concentrated (some numbers
        much hotter than others).
        """
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # Get non-zero frequencies
        nonzero_freqs = frequencies[frequencies > 0]
        
        if len(nonzero_freqs) == 0:
            return 0.3
        
        # Calculate coefficient of variation (std/mean)
        freq_mean = np.mean(nonzero_freqs)
        freq_std = np.std(nonzero_freqs)
        
        if freq_mean == 0:
            return 0.3
        
        cv = freq_std / freq_mean
        
        # Higher CV = more concentrated = higher confidence
        # Normalize: typical CV ranges from 0.2 to 1.0
        confidence = min(cv / 1.0, 1.0)
        
        # Scale to 0.4-0.8 range
        confidence = 0.4 + (confidence * 0.4)
        
        return confidence


if __name__ == '__main__':
    # Test the strategy
    from config import get_lottery_config
    from models import Draw
    import numpy as np
    
    config = get_lottery_config('OPAP_JOKER')
    strategy = Strategy02_PureFrequency(config)
    
    # Create test draws
    draws = [
        Draw(str(i), None, 
             np.random.choice(range(1, 46), size=5, replace=False),
             np.array([np.random.randint(1, 21)]), 
             False)
        for i in range(100)
    ]
    
    # Make prediction
    prediction = strategy.predict(draws, 0, len(draws) - 1)
    
    print(f"Strategy: {prediction.strategy_name}")
    print(f"Main numbers: {prediction.main_numbers}")
    print(f"Confidence: {prediction.confidence_score:.2%}")