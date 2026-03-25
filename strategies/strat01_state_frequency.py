"""
Strategy 01: State Patterns + Frequency with Pattern Fit Weighting

Combines state machine pattern recognition with weighted number scoring:
- Frequency (80%): How often the number appears
- Pattern Fit (20%): How well it matches predicted OE/HL patterns

Uses OE and HL pattern constraints only (no sum constraint).
NO gap analysis - pure frequency focus.
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
    State Patterns + Frequency with Pattern Fit Strategy
    
    Uses Markov-like state machines for Odd/Even and High/Low pattern prediction.
    Selects numbers using weighted scoring:
    - Frequency (80%): Appearance frequency in window
    - Pattern Fit (20%): Match with predicted OE/HL patterns
    
    No sum constraint - only OE and HL patterns enforced.
    No gap analysis - focuses purely on frequency.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT01", "State Patterns + Frequency")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
        self.state_machine = StateMachine(lottery_config)
        self.pattern_analyzer = PatternAnalyzer(lottery_config)
    
    def calculate_weighted_scores(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int,
        predicted_oe: str,
        predicted_hl: str
    ) -> List:
        """
        Calculate weighted score for each number
        
        Score = (Frequency × 0.8) + (Pattern Fit × 0.2)
        
        Returns:
            List of [number, score] pairs sorted by score descending
        """
        # Get frequencies
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        total_draws = end_idx - start_idx + 1
        
        # Calculate scores
        scores = []
        mid_point = self.config.main_pool // 2
        
        # Parse predicted patterns (e.g., "3O2E" means 3 odd, 2 even)
        predicted_odd_count = int(predicted_oe[0])
        predicted_even_count = int(predicted_oe[2])
        predicted_low_count = int(predicted_hl[0])
        predicted_high_count = int(predicted_hl[2])
        
        for num in range(1, self.config.main_pool + 1):
            # 1. Frequency Score (0-1): normalized frequency
            freq_score = frequencies[num] / total_draws if total_draws > 0 else 0
            
            # 2. Pattern Fit Score (0-1): how well number fits predicted patterns
            is_odd = (num % 2 == 1)
            is_low = (num <= mid_point)
            
            # Calculate OE fit
            oe_fit = 0.0
            if is_odd and predicted_odd_count > 0:
                oe_fit = 1.0
            elif not is_odd and predicted_even_count > 0:
                oe_fit = 1.0
            else:
                oe_fit = 0.5  # Neutral if pattern needs both
            
            # Calculate HL fit
            hl_fit = 0.0
            if is_low and predicted_low_count > 0:
                hl_fit = 1.0
            elif not is_low and predicted_high_count > 0:
                hl_fit = 1.0
            else:
                hl_fit = 0.5
            
            # Average OE and HL fit
            pattern_fit_score = (oe_fit + hl_fit) / 2
            
            # 3. Calculate weighted final score (80% frequency, 20% pattern fit)
            final_score = (
                freq_score * 0.8 +
                pattern_fit_score * 0.2
            )
            
            scores.append([num, final_score])
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores
    
    def select_numbers_by_score(
        self,
        scores: List,
        predicted_oe: str,
        predicted_hl: str,
        count: int
    ) -> List[int]:
        """
        Select top numbers by score that match OE/HL patterns
        
        Args:
            scores: List of [number, score] pairs sorted by score
            predicted_oe: e.g., "3O2E"
            predicted_hl: e.g., "2L3H"
            count: How many numbers to select
            
        Returns:
            List of selected numbers
        """
        # Parse target patterns
        target_odd = int(predicted_oe[0])
        target_even = int(predicted_oe[2])
        target_low = int(predicted_hl[0])
        target_high = int(predicted_hl[2])
        
        mid_point = self.config.main_pool // 2
        
        # Greedy selection with pattern constraints
        selected = []
        current_odd = 0
        current_even = 0
        current_low = 0
        current_high = 0
        
        for num, score in scores:
            if len(selected) >= count:
                break
            
            is_odd = (num % 2 == 1)
            is_low = (num <= mid_point)
            
            # Check if adding this number would violate constraints
            would_exceed_odd = is_odd and current_odd >= target_odd
            would_exceed_even = (not is_odd) and current_even >= target_even
            would_exceed_low = is_low and current_low >= target_low
            would_exceed_high = (not is_low) and current_high >= target_high
            
            if would_exceed_odd or would_exceed_even or would_exceed_low or would_exceed_high:
                continue
            
            # Add number
            selected.append(num)
            if is_odd:
                current_odd += 1
            else:
                current_even += 1
            if is_low:
                current_low += 1
            else:
                current_high += 1
        
        # If we couldn't fill all slots (too constrained), fill with highest scores
        if len(selected) < count:
            for num, score in scores:
                if num not in selected:
                    selected.append(num)
                    if len(selected) >= count:
                        break
        
        return selected
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using state patterns and weighted scoring"""
        
        # 1. Build state machines
        self.state_machine.build_from_draws(draws, start_idx, end_idx)
        
        # 2. Get current patterns
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        
        # 3. Calculate streaks
        oe_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'OE')
        hl_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'HL')
        
        # 4. Predict next patterns (OE and HL only, no sum constraint)
        predicted_oe = self.state_machine.predict_next_pattern(current_oe, 'OE', oe_streak)
        predicted_hl = self.state_machine.predict_next_pattern(current_hl, 'HL', hl_streak)
        
        # 5. Calculate weighted scores for all numbers
        scores = self.calculate_weighted_scores(
            draws, start_idx, end_idx,
            predicted_oe, predicted_hl
        )
        
        # 6. Select numbers by score (respecting OE/HL patterns only)
        main_numbers = self.select_numbers_by_score(
            scores,
            predicted_oe,
            predicted_hl,
            self.config.main_play_count
        )
        
        # 7. Predict bonus numbers (will be filled by joker predictor)
        bonus_numbers = [self.config.bonus_pool // 2]  # Placeholder
        
        # 8. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx)
        
        # 9. Calculate sum bracket from selected numbers (derived, not predicted)
        actual_sum = sum(main_numbers)
        bracket_start = (actual_sum // 20) * 20
        predicted_sum = f"{bracket_start}-{bracket_start + 19}"
        
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
                'hl_streak': hl_streak,
                'top_scores': scores[:15]  # Top 15 scored numbers for reference
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