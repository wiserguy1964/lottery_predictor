"""
Strategy 02: Temperature-Based Diversified Selection

Categorizes numbers as HOT/WARM/COLD and selects from all zones.
Uses HL pattern prediction for structural constraint.
"""
from typing import List, Dict, Tuple
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from analyzers.frequency_analyzer import FrequencyAnalyzer, PatternAnalyzer
from analyzers.state_machine import StateMachine
from config import LotteryConfig


class Strategy02_PureFrequency(BaseStrategy):
    """
    Temperature-Based Diversified Strategy
    
    Categorizes numbers into HOT/WARM/COLD based on frequency.
    Selects diverse mix: 5 HOT + 3 WARM + 1 COLD.
    Uses HL pattern prediction for structural constraint.
    
    Philosophy: Balance proven hot numbers with warming/cold numbers
    for diversification, respecting predicted HL structure.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT02", "Temperature Zones (Hot/Warm/Cold)")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
        self.pattern_analyzer = PatternAnalyzer(lottery_config)
        self.state_machine = StateMachine(lottery_config)
    
    def categorize_by_temperature(
        self,
        frequencies: np.ndarray
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        Categorize numbers into HOT/WARM/COLD based on frequency
        
        Uses percentile-based approach (top 33%, middle 33%, bottom 33%)
        
        Args:
            frequencies: Array of appearance counts per number
            
        Returns:
            Dict with 'HOT', 'WARM', 'COLD' lists of (number, frequency) tuples
        """
        # Create list of (number, frequency) pairs
        num_freq_pairs = [(num, int(frequencies[num])) 
                         for num in range(1, self.config.main_pool + 1)]
        
        # Sort by frequency descending
        num_freq_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Split into thirds
        total_numbers = len(num_freq_pairs)
        hot_count = total_numbers // 3
        warm_count = total_numbers // 3
        
        categories = {
            'HOT': num_freq_pairs[:hot_count],
            'WARM': num_freq_pairs[hot_count:hot_count + warm_count],
            'COLD': num_freq_pairs[hot_count + warm_count:]
        }
        
        return categories
    
    def select_from_category(
        self,
        category: List[Tuple[int, int]],
        count: int,
        needed_low: int,
        needed_high: int,
        already_selected: List[int]
    ) -> Tuple[List[int], int, int]:
        """
        Select numbers from a temperature category respecting HL constraints
        
        Args:
            category: List of (number, frequency) tuples from this category
            count: How many to select from this category
            needed_low: How many low numbers still needed
            needed_high: How many high numbers still needed
            already_selected: Numbers already selected
            
        Returns:
            (selected_numbers, remaining_low_needed, remaining_high_needed)
        """
        mid_point = self.config.main_pool // 2
        selected = []
        
        # Sort category by frequency (already sorted, but ensure)
        sorted_category = sorted(category, key=lambda x: x[1], reverse=True)
        
        for num, freq in sorted_category:
            if len(selected) >= count:
                break
            
            if num in already_selected:
                continue
            
            is_low = (num <= mid_point)
            
            # Check if we can add this number
            if is_low:
                if needed_low > 0:
                    selected.append(num)
                    needed_low -= 1
            else:  # is_high
                if needed_high > 0:
                    selected.append(num)
                    needed_high -= 1
        
        # If we couldn't fill quota due to constraints, add best remaining
        if len(selected) < count:
            for num, freq in sorted_category:
                if num not in already_selected and num not in selected:
                    selected.append(num)
                    if len(selected) >= count:
                        break
        
        return selected, needed_low, needed_high
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using temperature-based diversified selection"""
        
        # 1. Build state machine for HL pattern prediction
        self.state_machine.build_from_draws(draws, start_idx, end_idx)
        
        # 2. Get current HL pattern
        current_draw = draws[end_idx]
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        
        # 3. Calculate HL streak
        hl_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'HL')
        
        # 4. Predict next HL pattern
        predicted_hl = self.state_machine.predict_next_pattern(current_hl, 'HL', hl_streak)
        
        # 5. Get frequencies
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 6. Categorize numbers by temperature
        categories = self.categorize_by_temperature(frequencies)
        
        # 7. Parse HL pattern to get requirements
        # e.g., "3L2H" means 3 low, 2 high
        target_low = int(predicted_hl[0])
        target_high = int(predicted_hl[2])
        
        # 8. Select from each category: 5 HOT + 3 WARM + 1 COLD
        main_numbers = []
        needed_low = target_low
        needed_high = target_high
        
        # Select 5 from HOT
        hot_selected, needed_low, needed_high = self.select_from_category(
            categories['HOT'], 5, needed_low, needed_high, main_numbers
        )
        main_numbers.extend(hot_selected)
        
        # Select 3 from WARM
        warm_selected, needed_low, needed_high = self.select_from_category(
            categories['WARM'], 3, needed_low, needed_high, main_numbers
        )
        main_numbers.extend(warm_selected)
        
        # Select 1 from COLD
        cold_selected, needed_low, needed_high = self.select_from_category(
            categories['COLD'], 1, needed_low, needed_high, main_numbers
        )
        main_numbers.extend(cold_selected)
        
        # 9. Predict OE pattern (derive from selected numbers, not constrained)
        num_odd = sum(1 for n in main_numbers if n % 2 == 1)
        num_even = len(main_numbers) - num_odd
        predicted_oe = f"{num_odd}O{num_even}E"
        
        # 10. Calculate sum bracket (derive from selected numbers)
        actual_sum = sum(main_numbers)
        bracket_start = (actual_sum // 20) * 20
        predicted_sum = f"{bracket_start}-{bracket_start + 19}"
        
        # 11. Predict bonus numbers (placeholder)
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 12. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx)
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,  # Derived, not predicted
            predicted_hl=predicted_hl,  # Predicted via state machine
            predicted_sum_bracket=predicted_sum,  # Derived
            confidence_score=confidence,
            metadata={
                'hot_count': len(hot_selected),
                'warm_count': len(warm_selected),
                'cold_count': len(cold_selected),
                'current_hl': current_hl,
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
        Calculate confidence based on:
        - Frequency concentration (hot numbers vs others)
        - HL pattern consistency
        
        Higher confidence when:
        - Clear hot/cold separation
        - Stable HL patterns
        """
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 1. Frequency concentration score
        nonzero_freqs = frequencies[frequencies > 0]
        
        if len(nonzero_freqs) == 0:
            freq_score = 0.3
        else:
            freq_mean = np.mean(nonzero_freqs)
            freq_std = np.std(nonzero_freqs)
            
            if freq_mean == 0:
                freq_score = 0.3
            else:
                cv = freq_std / freq_mean
                freq_score = min(cv / 1.0, 1.0)
        
        # 2. HL pattern consistency score
        hl_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'HL', start_idx, end_idx)
        total_draws = sum(hl_freqs.values())
        
        if total_draws == 0:
            hl_score = 0.2
        else:
            hl_score = max(hl_freqs.values()) / total_draws if hl_freqs else 0.2
        
        # 3. Combine scores
        confidence = (freq_score * 0.6 + hl_score * 0.4)
        
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