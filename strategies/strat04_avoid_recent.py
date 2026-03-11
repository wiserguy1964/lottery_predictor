"""
Strategy 04: Avoid Recent Numbers
Frequency-based with penalty for recent appearances
"""
from typing import List
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from analyzers.frequency_analyzer import FrequencyAnalyzer
from config import LotteryConfig


class Strategy04_AvoidRecent(BaseStrategy):
    """
    Avoid Recent Numbers Strategy
    
    Uses frequency analysis but penalizes numbers that appeared in
    the last 5 draws to counter "hot number" streaks.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT04", "Avoid Recent Numbers")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
        self.lookback = 5  # Penalize last 5 draws
        self.penalty = 0.3  # Reduce frequency to 30%
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction avoiding recently drawn numbers"""
        
        # 1. Get base frequencies
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx).copy()
        
        # 2. Get recent numbers (last 5 draws)
        recent_start = max(start_idx, end_idx - self.lookback + 1)
        recent_numbers = self.freq_analyzer.get_recent_numbers(
            draws[recent_start:end_idx + 1],
            lookback=self.lookback
        )
        
        # 3. Penalize recent numbers
        for num in recent_numbers:
            if 1 <= num <= self.config.main_pool:
                frequencies[num] = int(frequencies[num] * self.penalty)
        
        # 4. Select top numbers after penalty
        # Sort by frequency
        number_freq_pairs = [(num, freq) for num, freq in enumerate(frequencies[1:], start=1)]
        number_freq_pairs.sort(key=lambda x: -x[1])
        
        # Select top N
        main_numbers = [num for num, freq in number_freq_pairs[:self.config.main_play_count]]
        main_numbers.sort()
        
        # 5. Get current patterns (no prediction)
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        current_sum_bracket = current_draw.get_sum_bracket()
        
        # 6. Predict bonus
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 7. Calculate confidence
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
                'recent_numbers': list(recent_numbers),
                'penalty_applied': self.penalty
            }
        )
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> float:
        """
        Confidence based on how many numbers were recently repeated
        
        Higher confidence when many numbers were repeated (stronger recency bias to counter)
        """
        if end_idx - start_idx < 10:
            return 0.5
        
        # Get recent numbers
        recent_start = max(start_idx, end_idx - self.lookback + 1)
        recent_numbers = self.freq_analyzer.get_recent_numbers(
            draws[recent_start:end_idx + 1],
            lookback=self.lookback
        )
        
        # More recent numbers = higher confidence this strategy will help
        recency_ratio = len(recent_numbers) / (self.lookback * self.config.main_count)
        
        # Scale to 0.4-0.8 range
        confidence = 0.4 + (min(recency_ratio, 1.0) * 0.4)
        
        return confidence