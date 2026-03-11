"""
Data models for lottery draws and predictions

Classes:
    - Draw: Represents a single lottery draw with main and bonus numbers
    - Prediction: Represents a strategy's prediction with patterns and confidence
    
Helper Functions:
    - parse_sum_bracket: Parse sum bracket string to min/max values
    - get_all_oe_patterns: Get all possible OE patterns
    - get_all_hl_patterns: Get all possible HL patterns
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional
import numpy as np


@dataclass
class Draw:
    """Single lottery draw with main numbers and bonus numbers"""
    draw_id: str
    date: Optional[datetime]
    main_numbers: np.ndarray  # Shape: (main_count,)
    bonus_numbers: np.ndarray  # Shape: (bonus_count,)
    jackpot_won: bool = False
    
    def __post_init__(self):
        """Ensure arrays are numpy arrays"""
        if not isinstance(self.main_numbers, np.ndarray):
            self.main_numbers = np.array(self.main_numbers, dtype=int)
        if not isinstance(self.bonus_numbers, np.ndarray):
            self.bonus_numbers = np.array(self.bonus_numbers, dtype=int)
    
    @property
    def all_numbers(self) -> np.ndarray:
        """Get all numbers (main + bonus) as single array"""
        return np.concatenate([self.main_numbers, self.bonus_numbers])
    
    def get_oe_pattern(self, pool_size: int = 45) -> str:
        """Calculate Odd/Even pattern for main numbers"""
        odd_count = np.sum(self.main_numbers % 2 == 1)
        even_count = len(self.main_numbers) - odd_count
        return f"{odd_count}O{even_count}E"
    
    def get_hl_pattern(self, pool_size: int = 45) -> str:
        """Calculate High/Low pattern for main numbers"""
        threshold = pool_size // 2
        low_count = np.sum(self.main_numbers <= threshold)
        high_count = len(self.main_numbers) - low_count
        return f"{low_count}L{high_count}H"
    
    def get_sum(self) -> int:
        """Get sum of main numbers"""
        return int(np.sum(self.main_numbers))
    
    def get_sum_bracket(self) -> str:
        """Get sum bracket (range) for main numbers"""
        total = self.get_sum()
        
        if total < 60:
            return "40-59"
        elif total < 80:
            return "60-79"
        elif total < 100:
            return "80-99"
        elif total < 120:
            return "100-119"
        elif total < 140:
            return "120-139"
        elif total < 160:
            return "140-159"
        elif total < 180:
            return "160-179"
        else:
            return "180-200"
    
    def get_bonus_oe(self) -> str:
        """Get Odd/Even for first bonus number"""
        if len(self.bonus_numbers) == 0:
            return "UNKNOWN"
        return "ODD" if self.bonus_numbers[0] % 2 == 1 else "EVEN"
    
    def get_bonus_hl(self, bonus_pool: int = 20) -> str:
        """Get High/Low for first bonus number"""
        if len(self.bonus_numbers) == 0:
            return "UNKNOWN"
        threshold = bonus_pool // 2
        return "LOW" if self.bonus_numbers[0] <= threshold else "HIGH"
    
    def get_bonus_range(self, bonus_pool: int = 20) -> str:
        """Get range bracket for first bonus number"""
        if len(self.bonus_numbers) == 0:
            return "UNKNOWN"
        
        bonus = self.bonus_numbers[0]
        bracket_size = bonus_pool // 4
        
        if bonus <= bracket_size:
            return f"1-{bracket_size}"
        elif bonus <= bracket_size * 2:
            return f"{bracket_size + 1}-{bracket_size * 2}"
        elif bonus <= bracket_size * 3:
            return f"{bracket_size * 2 + 1}-{bracket_size * 3}"
        else:
            return f"{bracket_size * 3 + 1}-{bonus_pool}"
    
    def __repr__(self) -> str:
        return (f"Draw(id={self.draw_id}, "
                f"main={list(self.main_numbers)}, "
                f"bonus={list(self.bonus_numbers)})")


@dataclass
class Prediction:
    """Prediction result from a strategy"""
    strategy_id: str
    strategy_name: str
    main_numbers: List[int]
    bonus_numbers: List[int]
    predicted_oe: str
    predicted_hl: str
    predicted_sum_bracket: str
    confidence_score: float
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def evaluate_against_draw(self, draw: Draw) -> dict:
        """Evaluate this prediction against an actual draw"""
        # Count main number matches
        main_matches = len(set(self.main_numbers) & set(draw.main_numbers))
        
        # Count bonus matches (handle both lists and single values)
        pred_bonus = self.bonus_numbers if isinstance(self.bonus_numbers, (list, tuple)) else [self.bonus_numbers]
        draw_bonus = draw.bonus_numbers if isinstance(draw.bonus_numbers, (list, tuple, np.ndarray)) else [draw.bonus_numbers]
        bonus_matches = len(set(pred_bonus) & set(draw_bonus))
        
        # Check pattern accuracy
        actual_oe = draw.get_oe_pattern()
        actual_hl = draw.get_hl_pattern()
        actual_sum = draw.get_sum_bracket()
        
        oe_correct = (self.predicted_oe == actual_oe)
        hl_correct = (self.predicted_hl == actual_hl)
        sum_correct = (self.predicted_sum_bracket == actual_sum)
        
        return {
            'main_matches': main_matches,
            'bonus_matches': bonus_matches,
            'oe_correct': oe_correct,
            'hl_correct': hl_correct,
            'sum_correct': sum_correct,
            'pattern_accuracy': sum([oe_correct, hl_correct, sum_correct]) / 3
        }


def parse_sum_bracket(bracket: str) -> Tuple[int, int]:
    """Parse sum bracket string to min/max values"""
    parts = bracket.split('-')
    if len(parts) != 2:
        raise ValueError(f"Invalid bracket format: {bracket}")
    
    return int(parts[0]), int(parts[1])


def get_all_oe_patterns(main_count: int = 5) -> List[str]:
    """Get all possible OE patterns for given main count"""
    patterns = []
    for odd in range(main_count + 1):
        even = main_count - odd
        patterns.append(f"{odd}O{even}E")
    return patterns


def get_all_hl_patterns(main_count: int = 5) -> List[str]:
    """Get all possible HL patterns for given main count"""
    patterns = []
    for low in range(main_count + 1):
        high = main_count - low
        patterns.append(f"{low}L{high}H")
    return patterns


__all__ = [
    'Draw',
    'Prediction',
    'parse_sum_bracket',
    'get_all_oe_patterns',
    'get_all_hl_patterns'
]

__version__ = '1.0.0'
