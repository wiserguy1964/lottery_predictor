"""
Strategy 01: State Patterns + Frequency (Original Algorithm)
Combines state machine pattern recognition with frequency analysis
"""
from typing import List
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction, parse_sum_bracket
from analyzers.frequency_analyzer import FrequencyAnalyzer, PatternAnalyzer
from analyzers.state_machine import StateMachine
from config import LotteryConfig


class Strategy01_StatePatternFreq(BaseStrategy):
    """
    State Patterns + Frequency Strategy
    
    Uses Markov-like state machines for Odd/Even, High/Low, and Sum Bracket patterns.
    Selects numbers based on frequency while matching predicted patterns.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT01", "State Patterns + Frequency")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
        self.state_machine = StateMachine(lottery_config)
        self.pattern_analyzer = PatternAnalyzer(lottery_config)
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using state patterns and frequency"""
        
        # 1. Build state machines
        self.state_machine.build_from_draws(draws, start_idx, end_idx)
        
        # 2. Get current patterns
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        current_sum_bracket = current_draw.get_sum_bracket()
        
        # 3. Calculate streaks
        oe_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'OE')
        hl_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'HL')
        
        # 4. Predict next patterns using state machine
        predicted_oe = self.state_machine.predict_next_pattern(current_oe, 'OE', oe_streak)
        predicted_hl = self.state_machine.predict_next_pattern(current_hl, 'HL', hl_streak)
        predicted_sum = self.state_machine.predict_next_pattern(current_sum_bracket, 'SUM', 0)
        
        # 5. Get frequencies
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 6. Select numbers matching predicted patterns
        sum_range = parse_sum_bracket(predicted_sum)
        main_numbers = self.select_numbers_with_constraints(
            frequencies,
            predicted_oe,
            predicted_hl,
            sum_range,
            self.config.main_play_count
        )
        
        # 7. Predict bonus numbers (will be filled by joker predictor)
        bonus_numbers = [self.config.bonus_pool // 2]  # Placeholder
        
        # 8. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx)
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,
            predicted_hl=predicted_hl,
            predicted_sum_bracket=predicted_sum,
            confidence_score=confidence,
            metadata={
                'current_oe': current_oe,
                'current_hl': current_hl,
                'oe_streak': oe_streak,
                'hl_streak': hl_streak
            }
        )
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> float:
        """
        Calculate confidence based on pattern stability
        
        Higher confidence when:
        - Patterns are stable (consistent)
        - Frequencies are concentrated (not uniform)
        """
        if end_idx - start_idx < 20:
            return 0.5  # Not enough data
        
        # Pattern consistency score
        oe_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'OE', start_idx, end_idx)
        hl_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'HL', start_idx, end_idx)
        
        # Calculate entropy (lower = more consistent)
        total_draws = sum(oe_freqs.values())
        if total_draws == 0:
            return 0.5
        
        oe_consistency = max(oe_freqs.values()) / total_draws if oe_freqs else 0.2
        hl_consistency = max(hl_freqs.values()) / total_draws if hl_freqs else 0.2
        
        # Frequency concentration
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        total_appearances = np.sum(frequencies[1:])
        if total_appearances == 0:
            return 0.5
        
        # Calculate coefficient of variation
        nonzero_freqs = frequencies[frequencies > 0]
        if len(nonzero_freqs) == 0:
            freq_concentration = 0
        else:
            freq_std = np.std(nonzero_freqs)
            freq_mean = np.mean(nonzero_freqs)
            freq_concentration = (freq_std / freq_mean) if freq_mean > 0 else 0
        
        # Combine metrics
        pattern_score = (oe_consistency + hl_consistency) / 2
        freq_score = min(freq_concentration, 1.0)
        
        confidence = (pattern_score * 0.6 + freq_score * 0.4)
        
        # Cap between 0.3 and 0.9
        return max(0.3, min(0.9, confidence))


if __name__ == '__main__':
    # Test the strategy
    from config import get_lottery_config
    from models import Draw
    import numpy as np
    
    config = get_lottery_config('OPAP_JOKER')
    strategy = Strategy01_StatePatternFreq(config)
    
    # Create test draws
    draws = [
        Draw("1", None, np.array([5, 12, 23, 34, 41]), np.array([10]), False),
        Draw("2", None, np.array([3, 12, 24, 35, 42]), np.array([15]), False),
        Draw("3", None, np.array([7, 13, 25, 36, 43]), np.array([8]), False),
        Draw("4", None, np.array([2, 14, 26, 37, 44]), np.array([12]), False),
        Draw("5", None, np.array([9, 15, 27, 38, 45]), np.array([5]), False),
    ]
    
    # Make prediction
    prediction = strategy.predict(draws, 0, len(draws) - 1)
    
    print(f"Strategy: {prediction.strategy_name}")
    print(f"Main numbers: {prediction.main_numbers}")
    print(f"Bonus numbers: {prediction.bonus_numbers}")
    print(f"Predicted OE: {prediction.predicted_oe}")
    print(f"Predicted HL: {prediction.predicted_hl}")
    print(f"Predicted Sum: {prediction.predicted_sum_bracket}")
    print(f"Confidence: {prediction.confidence_score:.2%}")