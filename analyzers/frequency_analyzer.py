"""
Analyzers for frequency and pattern analysis
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter

from models import Draw
from config import LotteryConfig


class FrequencyAnalyzer:
    """Analyzes number frequencies in draw history"""
    
    def __init__(self, lottery_config: LotteryConfig):
        """
        Initialize analyzer
        
        Args:
            lottery_config: Lottery configuration
        """
        self.config = lottery_config
    
    def get_main_frequencies(
        self,
        draws: List[Draw],
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> np.ndarray:
        """
        Get frequency of each main number in the specified range
        
        Args:
            draws: List of draws
            start_idx: Start index (inclusive)
            end_idx: End index (inclusive, None = last draw)
            
        Returns:
            Array of frequencies, index 0 unused, index 1-pool_size has counts
        """
        if end_idx is None:
            end_idx = len(draws) - 1
        
        # Create frequency array (1-indexed, so size+1)
        frequencies = np.zeros(self.config.main_pool + 1, dtype=int)
        
        for i in range(start_idx, end_idx + 1):
            if i < len(draws):
                for number in draws[i].main_numbers:
                    frequencies[number] += 1
        
        return frequencies
    
    def get_bonus_frequencies(
        self,
        draws: List[Draw],
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> np.ndarray:
        """
        Get frequency of each bonus number
        
        Args:
            draws: List of draws
            start_idx: Start index (inclusive)
            end_idx: End index (inclusive, None = last draw)
            
        Returns:
            Array of frequencies
        """
        if end_idx is None:
            end_idx = len(draws) - 1
        
        frequencies = np.zeros(self.config.bonus_pool + 1, dtype=int)
        
        for i in range(start_idx, end_idx + 1):
            if i < len(draws):
                for number in draws[i].bonus_numbers:
                    frequencies[number] += 1
        
        return frequencies
    
    def get_hot_numbers(
        self,
        draws: List[Draw],
        count: int = 12,
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> List[int]:
        """
        Get the hottest (most frequent) main numbers
        
        Args:
            draws: List of draws
            count: Number of hot numbers to return
            start_idx: Start index
            end_idx: End index
            
        Returns:
            List of hot numbers, sorted by frequency (descending)
        """
        frequencies = self.get_main_frequencies(draws, start_idx, end_idx)
        
        # Create (number, frequency) pairs, skip index 0
        number_freq = [(num, freq) for num, freq in enumerate(frequencies[1:], start=1)]
        
        # Sort by frequency (descending), then by number (ascending) for tie-breaking
        number_freq.sort(key=lambda x: (-x[1], x[0]))
        
        return [num for num, freq in number_freq[:count]]
    
    def get_cold_numbers(
        self,
        draws: List[Draw],
        count: int = 12,
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> List[int]:
        """
        Get the coldest (least frequent) main numbers
        
        Args:
            draws: List of draws
            count: Number of cold numbers to return
            start_idx: Start index
            end_idx: End index
            
        Returns:
            List of cold numbers, sorted by frequency (ascending)
        """
        frequencies = self.get_main_frequencies(draws, start_idx, end_idx)
        
        # Create (number, frequency) pairs
        number_freq = [(num, freq) for num, freq in enumerate(frequencies[1:], start=1)]
        
        # Sort by frequency (ascending), then by number (ascending)
        number_freq.sort(key=lambda x: (x[1], x[0]))
        
        return [num for num, freq in number_freq[:count]]
    
    def get_recent_numbers(
        self,
        draws: List[Draw],
        lookback: int = 5
    ) -> set:
        """
        Get numbers that appeared in recent draws
        
        Args:
            draws: List of draws
            lookback: Number of recent draws to check
            
        Returns:
            Set of numbers that appeared recently
        """
        recent = set()
        start = max(0, len(draws) - lookback)
        
        for i in range(start, len(draws)):
            recent.update(draws[i].main_numbers)
        
        return recent


class PatternAnalyzer:
    """Analyzes patterns (OE, HL, Sum) in draw history"""
    
    def __init__(self, lottery_config: LotteryConfig):
        """
        Initialize analyzer
        
        Args:
            lottery_config: Lottery configuration
        """
        self.config = lottery_config
    
    def get_pattern_frequencies(
        self,
        draws: List[Draw],
        pattern_type: str,
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Get frequency of each pattern
        
        Args:
            draws: List of draws
            pattern_type: 'OE', 'HL', or 'SUM'
            start_idx: Start index
            end_idx: End index
            
        Returns:
            Dictionary mapping pattern to frequency
        """
        if end_idx is None:
            end_idx = len(draws) - 1
        
        frequencies = defaultdict(int)
        
        for i in range(start_idx, min(end_idx + 1, len(draws))):
            if pattern_type == 'OE':
                pattern = draws[i].get_oe_pattern(self.config.main_pool)
            elif pattern_type == 'HL':
                pattern = draws[i].get_hl_pattern(self.config.main_pool)
            elif pattern_type == 'SUM':
                pattern = draws[i].get_sum_bracket()
            else:
                raise ValueError(f"Unknown pattern type: {pattern_type}")
            
            frequencies[pattern] += 1
        
        return dict(frequencies)
    
    def calculate_streak(
        self,
        draws: List[Draw],
        end_idx: int,
        pattern_type: str
    ) -> int:
        """
        Calculate how many consecutive draws have had the same pattern
        
        Args:
            draws: List of draws
            end_idx: Index to calculate streak from (going backwards)
            pattern_type: 'OE' or 'HL'
            
        Returns:
            Streak length
        """
        if end_idx < 0 or end_idx >= len(draws):
            return 0
        
        # Get pattern at end_idx
        if pattern_type == 'OE':
            current_pattern = draws[end_idx].get_oe_pattern(self.config.main_pool)
        elif pattern_type == 'HL':
            current_pattern = draws[end_idx].get_hl_pattern(self.config.main_pool)
        else:
            return 0
        
        streak = 1
        
        # Go backwards
        for i in range(end_idx - 1, -1, -1):
            if pattern_type == 'OE':
                pattern = draws[i].get_oe_pattern(self.config.main_pool)
            else:
                pattern = draws[i].get_hl_pattern(self.config.main_pool)
            
            if pattern == current_pattern:
                streak += 1
            else:
                break
        
        return streak
    
    def get_most_common_pattern(
        self,
        draws: List[Draw],
        pattern_type: str,
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> str:
        """
        Get the most common pattern in the range
        
        Args:
            draws: List of draws
            pattern_type: 'OE', 'HL', or 'SUM'
            start_idx: Start index
            end_idx: End index
            
        Returns:
            Most common pattern string
        """
        frequencies = self.get_pattern_frequencies(draws, pattern_type, start_idx, end_idx)
        
        if not frequencies:
            # Return default pattern
            if pattern_type == 'OE':
                return "2O3E"
            elif pattern_type == 'HL':
                return "3L2H"
            else:
                return "100-119"
        
        return max(frequencies.items(), key=lambda x: x[1])[0]


if __name__ == '__main__':
    # Test analyzers
    from config import get_lottery_config
    from models import Draw
    import numpy as np
    
    config = get_lottery_config('OPAP_JOKER')
    
    # Create some test draws
    draws = [
        Draw("1", None, np.array([5, 12, 23, 34, 41]), np.array([10]), False),
        Draw("2", None, np.array([3, 12, 24, 35, 42]), np.array([15]), False),
        Draw("3", None, np.array([7, 13, 25, 36, 43]), np.array([8]), False),
    ]
    
    # Test frequency analyzer
    freq_analyzer = FrequencyAnalyzer(config)
    frequencies = freq_analyzer.get_main_frequencies(draws)
    print("Main number frequencies:")
    for i in range(1, min(46, len(frequencies))):
        if frequencies[i] > 0:
            print(f"  {i}: {frequencies[i]}")
    
    hot = freq_analyzer.get_hot_numbers(draws, count=5)
    print(f"\nHot numbers: {hot}")
    
    # Test pattern analyzer
    pattern_analyzer = PatternAnalyzer(config)
    oe_freqs = pattern_analyzer.get_pattern_frequencies(draws, 'OE')
    print(f"\nOE pattern frequencies: {oe_freqs}")
    
    most_common_oe = pattern_analyzer.get_most_common_pattern(draws, 'OE')
    print(f"Most common OE: {most_common_oe}")