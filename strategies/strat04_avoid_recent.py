"""
Strategy 04: Recent Numbers with OE+HL Pattern
Embraces recent numbers as predictors with dual pattern constraints
"""
from typing import List, Set, Tuple
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from analyzers.frequency_analyzer import FrequencyAnalyzer, PatternAnalyzer
from analyzers.state_machine import StateMachine
from config import LotteryConfig


class Strategy04_AvoidRecent(BaseStrategy):
    """
    Recent Numbers Strategy with OE+HL Patterns
    
    Philosophy: Numbers from recent draws ARE good predictors!
    - Select from last 5 draws (most recent)
    - Include some from draws 6-10 back (pre-previous)
    - Use OE+HL state machines for pattern constraints
    
    CONFIGURABLE DISTRIBUTION:
    - Option A: 7 recent + 2 pre-previous (favor recency)
    - Option B: 6 recent + 3 pre-previous (balanced) - DEFAULT
    - Option C: 5 recent + 4 pre-previous (more diversity)
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT04", "Avoid Recent Numbers")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
        self.pattern_analyzer = PatternAnalyzer(lottery_config)
        self.state_machine = StateMachine(lottery_config)
        
        # Configuration - ADJUST THESE TO TEST DIFFERENT DISTRIBUTIONS
        self.recent_lookback = 5      # Last 5 draws
        self.preprevious_lookback = 5  # Draws 6-10 back
        
        # Distribution options (PROPORTIONS - scales with main_play_count automatically!):
        # Option A: More recent (78% recent, 22% pre-previous)
        # Option B: Balanced (67% recent, 33% pre-previous) - DEFAULT
        # Option C: More diversity (56% recent, 44% pre-previous)
        
        # Uncomment one:
        # self.recent_percentage = 0.78  # Option A: 78% from recent (e.g., 7 of 9)
        self.recent_percentage = 0.67  # Option B: 67% from recent (e.g., 6 of 9) - DEFAULT
        # self.recent_percentage = 0.56  # Option C: 56% from recent (e.g., 5 of 9)
        
        # Calculate actual counts dynamically based on main_play_count
        # This scales automatically: 9→6+3, 6→4+2, 15→10+5, etc.
        self.recent_count = int(self.config.main_play_count * self.recent_percentage)
        self.preprevious_count = self.config.main_play_count - self.recent_count
    
    def get_numbers_from_draws(
        self,
        draws: List[Draw],
        start_idx: int,
        count: int
    ) -> Set[int]:
        """
        Extract all unique numbers from a range of draws
        
        Args:
            draws: List of draws
            start_idx: Starting index (inclusive)
            count: Number of draws to look at
            
        Returns:
            Set of unique numbers from those draws
        """
        numbers = set()
        end_idx = min(start_idx + count, len(draws))
        
        for i in range(start_idx, end_idx):
            if i < len(draws):
                numbers.update(draws[i].main_numbers)
        
        return numbers
    
    def select_from_pool(
        self,
        pool: Set[int],
        count: int,
        frequencies: np.ndarray,
        needed_odd: int,
        needed_even: int,
        needed_low: int,
        needed_high: int,
        already_selected: Set[int]
    ) -> Tuple[List[int], int, int, int, int]:
        """
        Select numbers from pool respecting BOTH OE and HL constraints
        
        Args:
            pool: Set of candidate numbers
            count: How many to select
            frequencies: Frequency array for scoring
            needed_odd: How many odd numbers still needed
            needed_even: How many even numbers still needed
            needed_low: How many low numbers still needed
            needed_high: How many high numbers still needed
            already_selected: Numbers already selected
            
        Returns:
            (selected_numbers, remaining_odd, remaining_even, remaining_low, remaining_high)
        """
        mid_point = self.config.main_pool // 2
        
        # Convert pool to list with frequencies
        candidates = []
        for num in pool:
            if num not in already_selected and 1 <= num <= self.config.main_pool:
                freq = frequencies[num] if num < len(frequencies) else 0
                candidates.append((num, freq))
        
        # Sort by frequency descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        
        for num, freq in candidates:
            if len(selected) >= count:
                break
            
            is_odd = (num % 2 == 1)
            is_low = (num <= mid_point)
            
            # Check if we can add this number (must satisfy BOTH OE and HL constraints)
            can_add = False
            
            if is_odd and is_low:
                if needed_odd > 0 and needed_low > 0:
                    can_add = True
                    needed_odd -= 1
                    needed_low -= 1
            elif is_odd and not is_low:  # Odd + High
                if needed_odd > 0 and needed_high > 0:
                    can_add = True
                    needed_odd -= 1
                    needed_high -= 1
            elif not is_odd and is_low:  # Even + Low
                if needed_even > 0 and needed_low > 0:
                    can_add = True
                    needed_even -= 1
                    needed_low -= 1
            else:  # Even + High
                if needed_even > 0 and needed_high > 0:
                    can_add = True
                    needed_even -= 1
                    needed_high -= 1
            
            if can_add:
                selected.append(num)
        
        # If we couldn't fill quota due to constraints, add best remaining
        if len(selected) < count:
            for num, freq in candidates:
                if num not in selected:
                    selected.append(num)
                    if len(selected) >= count:
                        break
        
        return selected, needed_odd, needed_even, needed_low, needed_high
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using recent numbers with OE+HL patterns"""
        
        # 1. Build state machine for pattern predictions
        self.state_machine.build_from_draws(draws, start_idx, end_idx)
        
        # 2. Get current patterns
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        
        # 3. Calculate pattern streaks
        oe_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'OE')
        hl_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'HL')
        
        # 4. Predict next OE and HL patterns
        predicted_oe = self.state_machine.predict_next_pattern(current_oe, 'OE', oe_streak)
        predicted_hl = self.state_machine.predict_next_pattern(current_hl, 'HL', hl_streak)
        
        # 5. Get frequencies for scoring within pools
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 6. Get RECENT pool (last 5 draws)
        recent_start = max(0, end_idx - self.recent_lookback + 1)
        recent_pool = self.get_numbers_from_draws(draws, recent_start, self.recent_lookback)
        
        # 7. Get PRE-PREVIOUS pool (draws 6-10 back)
        preprevious_end = recent_start - 1
        preprevious_start = max(0, preprevious_end - self.preprevious_lookback + 1)
        preprevious_pool = self.get_numbers_from_draws(draws, preprevious_start, self.preprevious_lookback)
        
        # 8. Parse patterns to get requirements
        # e.g., "3O2E" means 3 odd, 2 even
        # e.g., "2L3H" means 2 low, 3 high
        target_odd = int(predicted_oe[0])
        target_even = int(predicted_oe[2])
        target_low = int(predicted_hl[0])
        target_high = int(predicted_hl[2])
        
        # 9. Select from RECENT pool first
        main_numbers = []
        needed_odd = target_odd
        needed_even = target_even
        needed_low = target_low
        needed_high = target_high
        
        recent_selected, needed_odd, needed_even, needed_low, needed_high = self.select_from_pool(
            recent_pool, self.recent_count, frequencies, 
            needed_odd, needed_even, needed_low, needed_high, set(main_numbers)
        )
        main_numbers.extend(recent_selected)
        
        # 10. Select from PRE-PREVIOUS pool
        preprevious_selected, needed_odd, needed_even, needed_low, needed_high = self.select_from_pool(
            preprevious_pool, self.preprevious_count, frequencies,
            needed_odd, needed_even, needed_low, needed_high, set(main_numbers)
        )
        main_numbers.extend(preprevious_selected)
        
        # 11. If we still don't have enough, fill from all numbers in window
        if len(main_numbers) < self.config.main_play_count:
            all_numbers = set(range(1, self.config.main_pool + 1))
            remaining_pool = all_numbers - set(main_numbers)
            
            remaining_needed = self.config.main_play_count - len(main_numbers)
            remaining_selected, _, _, _, _ = self.select_from_pool(
                remaining_pool, remaining_needed, frequencies,
                needed_odd, needed_even, needed_low, needed_high, set(main_numbers)
            )
            main_numbers.extend(remaining_selected)
        
        # 12. Calculate sum bracket (derive from selected numbers)
        actual_sum = sum(main_numbers)
        bracket_start = (actual_sum // 20) * 20
        predicted_sum = f"{bracket_start}-{bracket_start + 19}"
        
        # 13. Predict bonus numbers (placeholder)
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 14. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx, recent_pool, preprevious_pool)
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,  # Predicted via state machine
            predicted_hl=predicted_hl,  # Predicted via state machine (NEW!)
            predicted_sum_bracket=predicted_sum,  # Derived
            confidence_score=confidence,
            metadata={
                'recent_pool_size': len(recent_pool),
                'preprevious_pool_size': len(preprevious_pool),
                'recent_selected': len(recent_selected),
                'preprevious_selected': len(preprevious_selected),
                'current_oe': current_oe,
                'current_hl': current_hl,
                'oe_streak': oe_streak,
                'hl_streak': hl_streak,
                'distribution': f'{self.recent_count}R+{self.preprevious_count}P'
            }
        )
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int,
        recent_pool: Set[int],
        preprevious_pool: Set[int]
    ) -> float:
        """
        Calculate confidence based on:
        - Size of recent pool (more numbers = more choices = higher confidence)
        - OE+HL pattern consistency
        - Overlap between recent and pre-previous pools
        """
        # 1. Pool size score (larger pools = better)
        pool_size_ratio = len(recent_pool) / (self.recent_lookback * self.config.main_count)
        pool_score = min(pool_size_ratio, 1.0)
        
        # 2. OE pattern consistency
        oe_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'OE', start_idx, end_idx)
        oe_total = sum(oe_freqs.values())
        oe_score = max(oe_freqs.values()) / oe_total if oe_total > 0 else 0.2
        
        # 3. HL pattern consistency
        hl_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'HL', start_idx, end_idx)
        hl_total = sum(hl_freqs.values())
        hl_score = max(hl_freqs.values()) / hl_total if hl_total > 0 else 0.2
        
        # 4. Pool overlap (some overlap is good - continuity)
        overlap = recent_pool & preprevious_pool
        overlap_ratio = len(overlap) / max(len(recent_pool), 1)
        overlap_score = min(overlap_ratio * 2, 1.0)
        
        # 5. Combine scores (now includes both OE and HL)
        confidence = (pool_score * 0.3 + oe_score * 0.3 + hl_score * 0.3 + overlap_score * 0.1)
        
        # Scale to 0.4-0.8 range
        confidence = 0.4 + (confidence * 0.4)
        
        return confidence
