"""
Strategy 05: Sorted Position Transitions
Tracks number transitions in sorted positions with OE/HL constraints
"""
from typing import List, Dict, Tuple, Set
import numpy as np
from collections import defaultdict

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from analyzers.frequency_analyzer import FrequencyAnalyzer, PatternAnalyzer
from analyzers.state_machine import StateMachine
from config import LotteryConfig


class Strategy05_MarkovChain(BaseStrategy):
    """
    Sorted Position Transition Strategy
    
    Philosophy: Track what numbers appear in each sorted position
    after seeing a specific number in that position.
    
    Algorithm:
    1. Sort each draw in ascending order
    2. Track position-based transitions:
       - "After seeing number X in position i, 
          what appeared in position i next draw?"
    3. Predict using most common transitions
    4. Apply OE+HL pattern constraints
    
    Example:
      Draw 100 sorted: [5, 12, 23, 35, 42]
                        ↓   ↓   ↓   ↓   ↓
                       P1  P2  P3  P4  P5
      
      Draw 101 sorted: [3, 15, 28, 33, 44]
                        ↓   ↓   ↓   ↓   ↓
                       P1  P2  P3  P4  P5
      
      Transitions learned:
        P1: 5 → 3
        P2: 12 → 15
        P3: 23 → 28
        P4: 35 → 33
        P5: 42 → 44
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT05", "Markov Chain Prediction")
        self.freq_analyzer = FrequencyAnalyzer(lottery_config)
        self.pattern_analyzer = PatternAnalyzer(lottery_config)
        self.state_machine = StateMachine(lottery_config)
    
    def build_transition_table(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Dict[int, Dict[int, Dict[int, int]]]:
        """
        Build transition frequency table for sorted positions
        
        Returns:
            Dict[position][number][next_number] = count
            
        Example:
            transitions[0][5][3] = 2  means:
            "In position 0 (smallest), after seeing 5, 
             we saw 3 in position 0 next draw, 2 times"
        """
        transitions = {}
        
        # Initialize for each position
        for pos in range(self.config.main_count):
            transitions[pos] = defaultdict(lambda: defaultdict(int))
        
        # Build transition counts
        for i in range(start_idx, end_idx):
            if i + 1 >= len(draws):
                break
            
            current_sorted = sorted(draws[i].main_numbers)
            next_sorted = sorted(draws[i + 1].main_numbers)
            
            for pos in range(self.config.main_count):
                current_num = current_sorted[pos]
                next_num = next_sorted[pos]
                
                transitions[pos][current_num][next_num] += 1
        
        return transitions
    
    def predict_from_transitions(
        self,
        current_draw: Draw,
        transitions: Dict,
        frequencies: np.ndarray
    ) -> List[int]:
        """
        Predict numbers based on sorted position transitions
        
        Args:
            current_draw: Current draw to predict from
            transitions: Transition table
            frequencies: Frequency array for fallback
            
        Returns:
            List of predicted numbers (may have duplicates or gaps)
        """
        sorted_current = sorted(current_draw.main_numbers)
        predictions = []
        
        # Predict for each position based on transitions
        for pos in range(self.config.main_count):
            current_num = sorted_current[pos]
            
            if current_num in transitions[pos]:
                # Get transition counts for this number in this position
                trans_counts = transitions[pos][current_num]
                
                if trans_counts:
                    # Find most common transition
                    most_common_num = max(trans_counts.items(), key=lambda x: x[1])[0]
                    predictions.append(most_common_num)
                else:
                    # No transitions, use frequency
                    predictions.append(None)
            else:
                # Never seen this number in this position
                predictions.append(None)
        
        # Now we have up to 5 predictions (one per position)
        # Need to expand to main_play_count (9) using frequency
        
        # Remove None values
        valid_predictions = [p for p in predictions if p is not None]
        
        # Get additional numbers from frequency to reach main_play_count
        needed = self.config.main_play_count - len(valid_predictions)
        
        if needed > 0:
            # Get top frequent numbers not already predicted
            freq_candidates = []
            for num in range(1, self.config.main_pool + 1):
                if num not in valid_predictions:
                    freq_candidates.append((num, frequencies[num]))
            
            freq_candidates.sort(key=lambda x: x[1], reverse=True)
            additional = [num for num, freq in freq_candidates[:needed]]
            
            valid_predictions.extend(additional)
        
        return valid_predictions
    
    def _count_consecutives(self, numbers: List[int]) -> int:
        """
        Count the maximum consecutive run in a sorted list
        
        Args:
            numbers: Sorted list of numbers
            
        Returns:
            Maximum consecutive count (e.g., [15,16,17] returns 3)
        """
        if len(numbers) < 2:
            return 1
        
        sorted_nums = sorted(numbers)
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i-1] + 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def _breaks_consecutive_limit(self, selected: List[int], new_num: int, max_consecutive: int = 2) -> bool:
        """
        Check if adding new_num would create too many consecutives
        
        Args:
            selected: Currently selected numbers
            new_num: Number to potentially add
            max_consecutive: Maximum allowed consecutive run
            
        Returns:
            True if adding new_num would violate limit
        """
        test_list = sorted(selected + [new_num])
        return self._count_consecutives(test_list) > max_consecutive
    
    def select_with_constraints(
        self,
        candidate_numbers: List[int],
        frequencies: np.ndarray,
        target_odd: int,
        target_even: int,
        target_low: int,
        target_high: int
    ) -> List[int]:
        """
        Select final numbers respecting OE+HL constraints
        
        Args:
            candidate_numbers: Pool of predicted numbers
            frequencies: For scoring candidates
            target_odd/even/low/high: Pattern requirements
            
        Returns:
            List of main_play_count numbers matching constraints
        """
        mid_point = self.config.main_pool // 2
        
        # Score candidates by frequency
        scored = []
        for num in candidate_numbers:
            if 1 <= num <= self.config.main_pool:
                score = frequencies[num] if num < len(frequencies) else 0
                scored.append((num, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        needed_odd = target_odd
        needed_even = target_even
        needed_low = target_low
        needed_high = target_high
        
        # First pass: select numbers matching OE+HL+Consecutive constraints
        for num, score in scored:
            if len(selected) >= self.config.main_play_count:
                break
            
            if num in selected:
                continue
            
            is_odd = (num % 2 == 1)
            is_low = (num <= mid_point)
            
            # Check if this number satisfies constraints
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
                # Additional check: don't create 3+ consecutives
                if not self._breaks_consecutive_limit(selected, num, max_consecutive=2):
                    selected.append(num)
                else:
                    # Revert quota decrements since we're not adding
                    if is_odd and is_low:
                        needed_odd += 1
                        needed_low += 1
                    elif is_odd and not is_low:
                        needed_odd += 1
                        needed_high += 1
                    elif not is_odd and is_low:
                        needed_even += 1
                        needed_low += 1
                    else:
                        needed_even += 1
                        needed_high += 1
        
        # Second pass: if still need more, ignore OE+HL but keep consecutive limit
        if len(selected) < self.config.main_play_count:
            for num, score in scored:
                if num not in selected:
                    if not self._breaks_consecutive_limit(selected, num, max_consecutive=2):
                        selected.append(num)
                        if len(selected) >= self.config.main_play_count:
                            break
        
        # Third pass: if still need more, try again with ONLY consecutive check
        if len(selected) < self.config.main_play_count:
            for num, score in scored:
                if num not in selected:
                    if not self._breaks_consecutive_limit(selected, num, max_consecutive=2):
                        selected.append(num)
                        if len(selected) >= self.config.main_play_count:
                            break
        
        # ABSOLUTE FINAL fallback: if STILL not enough, ignore all constraints (rare)
        if len(selected) < self.config.main_play_count:
            for num, score in scored:
                if num not in selected:
                    selected.append(num)
                    if len(selected) >= self.config.main_play_count:
                        break
        
        return sorted(selected)
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using sorted position transitions"""
        
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
        
        # 5. Build transition table
        transitions = self.build_transition_table(draws, start_idx, end_idx)
        
        # 6. Get frequencies for fallback and scoring
        frequencies = self.freq_analyzer.get_main_frequencies(draws, start_idx, end_idx)
        
        # 7. Predict numbers from transitions
        candidate_numbers = self.predict_from_transitions(
            current_draw, transitions, frequencies
        )
        
        # 8. Parse pattern requirements
        target_odd = int(predicted_oe[0])
        target_even = int(predicted_oe[2])
        target_low = int(predicted_hl[0])
        target_high = int(predicted_hl[2])
        
        # 9. Select final numbers with OE+HL constraints
        main_numbers = self.select_with_constraints(
            candidate_numbers, frequencies,
            target_odd, target_even, target_low, target_high
        )
        
        # 10. Calculate sum bracket (derive from selected numbers)
        actual_sum = sum(main_numbers)
        bracket_start = (actual_sum // 20) * 20
        predicted_sum = f"{bracket_start}-{bracket_start + 19}"
        
        # 11. Predict bonus numbers (placeholder)
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 12. Calculate confidence
        confidence = self.calculate_confidence(draws, start_idx, end_idx, transitions)
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,  # Predicted via state machine
            predicted_hl=predicted_hl,  # Predicted via state machine
            predicted_sum_bracket=predicted_sum,  # Derived
            confidence_score=confidence,
            metadata={
                'transition_based': True,
                'sorted_positions': True,
                'current_oe': current_oe,
                'current_hl': current_hl,
                'oe_streak': oe_streak,
                'hl_streak': hl_streak,
                'consecutive_limit': 2,
                'constraints_applied': 'OE+HL+Consecutive'
            }
        )
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int,
        transitions: Dict
    ) -> float:
        """
        Calculate confidence based on transition data quality
        
        Higher confidence when:
        - More transition data available
        - Transitions are consistent (not random)
        """
        window_size = end_idx - start_idx + 1
        
        # 1. Window size score
        if window_size < 50:
            size_score = 0.3
        elif window_size < 100:
            size_score = 0.5
        else:
            size_score = 0.7
        
        # 2. Transition data quality score
        # Count how many positions have good transition data
        positions_with_data = 0
        total_transitions = 0
        
        for pos in range(self.config.main_count):
            if pos in transitions:
                for num in transitions[pos]:
                    trans_counts = transitions[pos][num]
                    if trans_counts:
                        positions_with_data += 1
                        total_transitions += sum(trans_counts.values())
                        break  # Just need to know position has data
        
        data_score = positions_with_data / self.config.main_count
        
        # 3. Pattern consistency (from pattern analyzer)
        oe_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'OE', start_idx, end_idx)
        hl_freqs = self.pattern_analyzer.get_pattern_frequencies(draws, 'HL', start_idx, end_idx)
        
        oe_total = sum(oe_freqs.values())
        hl_total = sum(hl_freqs.values())
        
        oe_score = max(oe_freqs.values()) / oe_total if oe_total > 0 else 0.2
        hl_score = max(hl_freqs.values()) / hl_total if hl_total > 0 else 0.2
        
        # 4. Combine scores
        confidence = (size_score * 0.2 + data_score * 0.3 + oe_score * 0.25 + hl_score * 0.25)
        
        # Scale to 0.4-0.8 range
        confidence = 0.4 + (confidence * 0.4)
        
        return confidence
