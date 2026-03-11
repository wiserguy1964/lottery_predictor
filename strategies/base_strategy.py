"""
Base strategy class that all prediction strategies inherit from
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

from models import Prediction
from config import LotteryConfig


class BaseStrategy(ABC):
    """Abstract base class for all prediction strategies"""
    
    def __init__(self, lottery_config: LotteryConfig, strategy_id: str, strategy_name: str):
        """
        Initialize strategy
        
        Args:
            lottery_config: Lottery configuration
            strategy_id: Unique strategy identifier
            strategy_name: Human-readable strategy name
        """
        self.config = lottery_config
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
    
    @abstractmethod
    def predict(
        self,
        draws: List,
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """
        Generate prediction for next draw
        
        Args:
            draws: List of Draw objects
            start_idx: Starting index for analysis window
            end_idx: Ending index for analysis window
            
        Returns:
            Prediction object
        """
        pass
    
    @abstractmethod
    def calculate_confidence(
        self,
        draws: List,
        start_idx: int,
        end_idx: int
    ) -> float:
        """
        Calculate confidence score for this strategy
        
        Args:
            draws: List of Draw objects
            start_idx: Starting index for analysis window
            end_idx: Ending index for analysis window
            
        Returns:
            Confidence score between 0 and 1
        """
        pass
    
    def select_numbers_with_constraints(
        self,
        frequencies: np.ndarray,
        target_oe: str,
        target_hl: str,
        sum_range: Tuple[int, int],
        count: int,
        max_iterations: int = 1000  # IMPORTANT: Prevent infinite loops
    ) -> List[int]:
        """
        Select numbers matching OE, HL, and sum constraints
        
        Uses a greedy algorithm with backtracking to find numbers
        that satisfy all constraints.
        
        Args:
            frequencies: Frequency array (1-indexed)
            target_oe: Target Odd/Even pattern (e.g., "2O3E")
            target_hl: Target High/Low pattern (e.g., "3L2H")
            sum_range: Target sum range (min, max)
            count: Number of numbers to select
            max_iterations: Maximum attempts before giving up
            
        Returns:
            List of selected numbers
        """
        # Parse patterns
        odd_target = int(target_oe[0])
        low_target = int(target_hl[0])
        threshold = self.config.main_pool // 2
        min_sum, max_sum = sum_range
        
        # Categorize numbers by OE and HL
        odd_low = []
        odd_high = []
        even_low = []
        even_high = []
        
        for num in range(1, self.config.main_pool + 1):
            freq = frequencies[num] if num < len(frequencies) else 0
            
            is_odd = (num % 2 == 1)
            is_low = (num <= threshold)
            
            if is_odd and is_low:
                odd_low.append((num, freq))
            elif is_odd and not is_low:
                odd_high.append((num, freq))
            elif not is_odd and is_low:
                even_low.append((num, freq))
            else:  # even and high
                even_high.append((num, freq))
        
        # Sort by frequency (descending)
        odd_low.sort(key=lambda x: -x[1])
        odd_high.sort(key=lambda x: -x[1])
        even_low.sort(key=lambda x: -x[1])
        even_high.sort(key=lambda x: -x[1])
        
        # Try to build a valid combination
        for attempt in range(max_iterations):
            selected = self._try_build_combination(
                odd_low, odd_high, even_low, even_high,
                odd_target, low_target, count, min_sum, max_sum,
                attempt
            )
            
            if selected is not None:
                return sorted(selected)
        
        # If we can't satisfy constraints, just return top frequency numbers
        print(f"  Warning: Could not satisfy constraints after {max_iterations} attempts")
        return self._fallback_selection(frequencies, count)
    
    def _try_build_combination(
        self,
        odd_low: List[Tuple[int, float]],
        odd_high: List[Tuple[int, float]],
        even_low: List[Tuple[int, float]],
        even_high: List[Tuple[int, float]],
        odd_target: int,
        low_target: int,
        count: int,
        min_sum: int,
        max_sum: int,
        seed: int
    ) -> List[int]:
        """
        Try to build a valid combination with given constraints
        
        Uses randomization based on seed to try different combinations
        """
        # Calculate how many from each group
        even_target = count - odd_target
        high_target = count - low_target
        
        # Solve system:
        # odd_low_count + odd_high_count = odd_target
        # even_low_count + even_high_count = even_target
        # odd_low_count + even_low_count = low_target
        # odd_high_count + even_high_count = high_target
        
        odd_low_count = min(odd_target, low_target)
        odd_high_count = odd_target - odd_low_count
        even_low_count = low_target - odd_low_count
        even_high_count = even_target - even_low_count
        
        # Ensure non-negative
        odd_low_count = max(0, odd_low_count)
        odd_high_count = max(0, odd_high_count)
        even_low_count = max(0, even_low_count)
        even_high_count = max(0, even_high_count)
        
        # Select numbers from each group
        selected = []
        
        # Add some randomness based on seed
        offset = seed % 3
        
        # Odd low
        for i in range(min(odd_low_count, len(odd_low))):
            idx = (i + offset) % len(odd_low)
            selected.append(odd_low[idx][0])
        
        # Odd high
        for i in range(min(odd_high_count, len(odd_high))):
            idx = (i + offset) % len(odd_high)
            selected.append(odd_high[idx][0])
        
        # Even low
        for i in range(min(even_low_count, len(even_low))):
            idx = (i + offset) % len(even_low)
            selected.append(even_low[idx][0])
        
        # Even high
        for i in range(min(even_high_count, len(even_high))):
            idx = (i + offset) % len(even_high)
            selected.append(even_high[idx][0])
        
        # Fill any remaining slots
        all_numbers = (
            [n for n, f in odd_low] +
            [n for n, f in odd_high] +
            [n for n, f in even_low] +
            [n for n, f in even_high]
        )
        
        for num in all_numbers:
            if len(selected) >= count:
                break
            if num not in selected:
                selected.append(num)
        
        # Check sum constraint
        if len(selected) == count:
            total = sum(selected)
            if min_sum <= total <= max_sum:
                return selected
        
        return None
    
    def _fallback_selection(self, frequencies: np.ndarray, count: int) -> List[int]:
        """Fallback: just select top frequency numbers"""
        # Create list of (number, frequency) pairs
        number_freq = [(i, freq) for i, freq in enumerate(frequencies[1:], start=1)]
        
        # Sort by frequency descending
        number_freq.sort(key=lambda x: -x[1])
        
        # Select top N
        selected = [num for num, freq in number_freq[:count]]
        
        return sorted(selected)
