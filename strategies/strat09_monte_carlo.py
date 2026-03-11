"""
Strategy 09: Monte Carlo Pattern Matching

Uses Monte Carlo simulation to find numbers that frequently appear in 
combinations matching historical patterns (OE, HL, sum ranges).

Generates random combinations of main_play_count numbers (not just the 
5 that will be drawn) to find numbers that naturally fit patterns.

Theory: Numbers that appear often in pattern-compliant combinations 
might have higher probability of being drawn.
"""

from typing import List, Dict, Tuple
import numpy as np
from collections import Counter

from models import Draw, Prediction
from strategies.base_strategy import BaseStrategy
from config import LotteryConfig


class Strategy09_MonteCarloPattern(BaseStrategy):
    """
    Monte Carlo simulation to find numbers appearing in pattern-matching combinations
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(
            lottery_config,
            "STRAT09",
            "Monte Carlo Pattern Match"
        )
        self.simulation_count = 5000  # Number of MC simulations per window (reduced for speed)
    
    def predict(self, draws: List[Draw], start_idx: int, end_idx: int) -> Prediction:
        """Generate prediction using Monte Carlo pattern matching"""
        
        # Analyze recent patterns
        recent_oe_patterns = self._get_recent_oe_patterns(draws, start_idx, end_idx)
        recent_hl_patterns = self._get_recent_hl_patterns(draws, start_idx, end_idx)
        recent_sum_ranges = self._get_recent_sum_ranges(draws, start_idx, end_idx)
        
        print(f"  Running {self.simulation_count:,} Monte Carlo simulations...")
        
        # Run Monte Carlo simulations
        number_frequency = Counter()
        successful_combos = 0
        
        for _ in range(self.simulation_count):
            # Generate random combination
            random_combo = np.random.choice(
                range(1, self.config.main_pool + 1),
                size=self.config.main_play_count,
                replace=False
            )
            random_combo = sorted(random_combo)
            
            # Check if it matches recent patterns
            if self._matches_patterns(
                random_combo,
                recent_oe_patterns,
                recent_hl_patterns,
                recent_sum_ranges
            ):
                # This combo matches patterns - count its numbers!
                successful_combos += 1
                for num in random_combo:
                    number_frequency[num] += 1
        
        # Get top numbers from successful simulations
        if number_frequency:
            top_numbers = [num for num, freq in number_frequency.most_common(self.config.main_play_count)]
        else:
            # Fallback if no successful combos (shouldn't happen with loose matching)
            top_numbers = list(np.random.choice(
                range(1, self.config.main_pool + 1),
                size=self.config.main_play_count,
                replace=False
            ))
        
        main_numbers = sorted(top_numbers[:self.config.main_play_count])
        
        # Calculate confidence based on success rate
        success_rate = successful_combos / self.simulation_count
        confidence = 0.4 + (success_rate * 0.5)  # 0.4 to 0.9 range
        confidence = max(0.3, min(0.9, confidence))
        
        # Predict patterns based on most common in recent history
        predicted_oe = self._predict_most_common_oe(recent_oe_patterns)
        predicted_hl = self._predict_most_common_hl(recent_hl_patterns)
        predicted_sum = self._predict_sum_bracket(recent_sum_ranges)
        
        # Bonus placeholder
        bonus_numbers = [self.config.bonus_pool // 2]
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=main_numbers,
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,
            predicted_hl=predicted_hl,
            predicted_sum_bracket=predicted_sum,
            confidence_score=confidence,
            metadata={
                'simulations': self.simulation_count,
                'successful_combos': successful_combos,
                'success_rate': f"{success_rate:.2%}"
            }
        )
    
    def _get_recent_oe_patterns(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[Tuple[int, int]]:
        """Get recent odd/even patterns"""
        patterns = []
        window_size = 10  # Last 10 draws
        
        for i in range(max(start_idx, end_idx - window_size + 1), end_idx + 1):
            if i >= len(draws):
                break
            draw = draws[i]
            num_odd = sum(1 for n in draw.main_numbers if n % 2 == 1)
            num_even = len(draw.main_numbers) - num_odd
            patterns.append((num_odd, num_even))
        
        return patterns
    
    def _get_recent_hl_patterns(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[Tuple[int, int]]:
        """Get recent high/low patterns"""
        patterns = []
        window_size = 10
        mid_point = self.config.main_pool // 2
        
        for i in range(max(start_idx, end_idx - window_size + 1), end_idx + 1):
            if i >= len(draws):
                break
            draw = draws[i]
            num_low = sum(1 for n in draw.main_numbers if n <= mid_point)
            num_high = len(draw.main_numbers) - num_low
            patterns.append((num_low, num_high))
        
        return patterns
    
    def _get_recent_sum_ranges(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[Tuple[int, int]]:
        """Get recent sum ranges"""
        sums = []
        window_size = 10
        
        for i in range(max(start_idx, end_idx - window_size + 1), end_idx + 1):
            if i >= len(draws):
                break
            draw = draws[i]
            total = sum(draw.main_numbers)
            sums.append(total)
        
        if not sums:
            return [(0, 0)]
        
        # Create ranges from the sums
        min_sum = min(sums)
        max_sum = max(sums)
        avg_sum = int(np.mean(sums))
        std_sum = int(np.std(sums))
        
        # Allow 1 standard deviation from mean
        lower = max(self.config.main_count, avg_sum - std_sum)
        upper = min(self.config.main_pool * self.config.main_count, avg_sum + std_sum)
        
        return [(lower, upper)]
    
    def _matches_patterns(
        self,
        combo: np.ndarray,
        oe_patterns: List[Tuple[int, int]],
        hl_patterns: List[Tuple[int, int]],
        sum_ranges: List[Tuple[int, int]]
    ) -> bool:
        """Check if combination matches recent patterns"""
        
        # Check OE pattern
        num_odd = sum(1 for n in combo if n % 2 == 1)
        num_even = len(combo) - num_odd
        oe_match = (num_odd, num_even) in oe_patterns
        
        # Allow +/- 1 flexibility for OE
        if not oe_match:
            for pattern_odd, pattern_even in oe_patterns:
                if abs(num_odd - pattern_odd) <= 1:
                    oe_match = True
                    break
        
        # Check HL pattern
        mid_point = self.config.main_pool // 2
        num_low = sum(1 for n in combo if n <= mid_point)
        num_high = len(combo) - num_low
        hl_match = (num_low, num_high) in hl_patterns
        
        # Allow +/- 1 flexibility for HL
        if not hl_match:
            for pattern_low, pattern_high in hl_patterns:
                if abs(num_low - pattern_low) <= 1:
                    hl_match = True
                    break
        
        # Check sum range
        total = sum(combo)
        sum_match = False
        for lower, upper in sum_ranges:
            if lower <= total <= upper:
                sum_match = True
                break
        
        # Must match at least 2 out of 3 patterns
        matches = sum([oe_match, hl_match, sum_match])
        return matches >= 2
    
    def _predict_most_common_oe(self, patterns: List[Tuple[int, int]]) -> str:
        """Predict most common OE pattern"""
        if not patterns:
            return "3O2E"
        
        most_common = Counter(patterns).most_common(1)[0][0]
        return f"{most_common[0]}O{most_common[1]}E"
    
    def _predict_most_common_hl(self, patterns: List[Tuple[int, int]]) -> str:
        """Predict most common HL pattern"""
        if not patterns:
            return "3L2H"
        
        most_common = Counter(patterns).most_common(1)[0][0]
        return f"{most_common[0]}L{most_common[1]}H"
    
    def _predict_sum_bracket(self, sum_ranges: List[Tuple[int, int]]) -> str:
        """Predict sum bracket"""
        if not sum_ranges:
            return "100-119"
        
        lower, upper = sum_ranges[0]
        avg = (lower + upper) // 2
        bracket_start = (avg // 20) * 20
        return f"{bracket_start}-{bracket_start + 19}"
    
    def calculate_confidence(self, draws: List[Draw], start_idx: int, end_idx: int) -> float:
        """Calculate confidence (done in predict)"""
        return 0.6
