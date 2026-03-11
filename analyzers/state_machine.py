"""
State machine for pattern transitions (Markov-like analysis)
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from models import Draw
from config import LotteryConfig


class StateMachine:
    """State machine for tracking and predicting pattern transitions"""
    
    def __init__(self, lottery_config: LotteryConfig):
        """
        Initialize state machine
        
        Args:
            lottery_config: Lottery configuration
        """
        self.config = lottery_config
        self.oe_transitions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.hl_transitions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.sum_transitions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.bonus_transitions: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    
    def build_from_draws(
        self,
        draws: List[Draw],
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ):
        """
        Build state machine from draw history
        
        Args:
            draws: List of draws
            start_idx: Start index
            end_idx: End index (inclusive)
        """
        if end_idx is None:
            end_idx = len(draws) - 1
        
        # Clear existing transitions
        self.oe_transitions.clear()
        self.hl_transitions.clear()
        self.sum_transitions.clear()
        self.bonus_transitions.clear()
        
        # Build transitions (need at least 2 draws)
        for i in range(start_idx, min(end_idx, len(draws) - 1)):
            current_draw = draws[i]
            next_draw = draws[i + 1]
            
            # OE transitions
            current_oe = current_draw.get_oe_pattern(self.config.main_pool)
            next_oe = next_draw.get_oe_pattern(self.config.main_pool)
            self.oe_transitions[current_oe][next_oe] += 1
            
            # HL transitions
            current_hl = current_draw.get_hl_pattern(self.config.main_pool)
            next_hl = next_draw.get_hl_pattern(self.config.main_pool)
            self.hl_transitions[current_hl][next_hl] += 1
            
            # Sum bracket transitions
            current_sum = current_draw.get_sum_bracket()
            next_sum = next_draw.get_sum_bracket()
            self.sum_transitions[current_sum][next_sum] += 1
            
            # Bonus transitions (if applicable)
            if len(current_draw.bonus_numbers) > 0 and len(next_draw.bonus_numbers) > 0:
                current_bonus = int(current_draw.bonus_numbers[0])
                next_bonus = int(next_draw.bonus_numbers[0])
                self.bonus_transitions[current_bonus][next_bonus] += 1
    
    def predict_next_pattern(
        self,
        current_pattern: str,
        pattern_type: str,
        streak: int = 0
    ) -> str:
        """
        Predict next pattern using state machine
        
        Args:
            current_pattern: Current pattern (e.g., "2O3E")
            pattern_type: 'OE', 'HL', or 'SUM'
            streak: Current streak length (for streak-breaking logic)
            
        Returns:
            Predicted next pattern
        """
        # Select appropriate transition dict
        if pattern_type == 'OE':
            transitions = self.oe_transitions
        elif pattern_type == 'HL':
            transitions = self.hl_transitions
        elif pattern_type == 'SUM':
            transitions = self.sum_transitions
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
        
        # Get transitions from current pattern
        if current_pattern not in transitions or not transitions[current_pattern]:
            # No data, return most balanced pattern
            if pattern_type == 'OE':
                return "2O3E"
            elif pattern_type == 'HL':
                return "3L2H"
            else:
                return "100-119"
        
        next_patterns = transitions[current_pattern]
        
        # Apply streak-breaking logic if streak is long
        if streak >= 3 and pattern_type in ['OE', 'HL']:
            # Favor patterns different from current
            # Remove current pattern from consideration or reduce its weight
            adjusted_patterns = {
                pattern: count * 0.5 if pattern == current_pattern else count
                for pattern, count in next_patterns.items()
            }
            next_patterns = adjusted_patterns
        
        # Find most likely next pattern
        total = sum(next_patterns.values())
        if total == 0:
            if pattern_type == 'OE':
                return "2O3E"
            elif pattern_type == 'HL':
                return "3L2H"
            else:
                return "100-119"
        
        # Return pattern with highest probability
        return max(next_patterns.items(), key=lambda x: x[1])[0]
    
    def predict_next_bonus(self, current_bonus: int) -> int:
        """
        Predict next bonus number using transitions
        
        Args:
            current_bonus: Current bonus number
            
        Returns:
            Predicted next bonus number
        """
        if current_bonus not in self.bonus_transitions or not self.bonus_transitions[current_bonus]:
            # No data, return middle value
            return self.config.bonus_pool // 2
        
        next_bonuses = self.bonus_transitions[current_bonus]
        
        # Find most likely next bonus
        return max(next_bonuses.items(), key=lambda x: x[1])[0]
    
    def get_transition_probability(
        self,
        from_pattern: str,
        to_pattern: str,
        pattern_type: str
    ) -> float:
        """
        Get probability of transitioning from one pattern to another
        
        Args:
            from_pattern: Starting pattern
            to_pattern: Ending pattern
            pattern_type: 'OE', 'HL', or 'SUM'
            
        Returns:
            Probability (0-1)
        """
        if pattern_type == 'OE':
            transitions = self.oe_transitions
        elif pattern_type == 'HL':
            transitions = self.hl_transitions
        elif pattern_type == 'SUM':
            transitions = self.sum_transitions
        else:
            return 0.0
        
        if from_pattern not in transitions or not transitions[from_pattern]:
            return 0.0
        
        next_patterns = transitions[from_pattern]
        total = sum(next_patterns.values())
        
        if total == 0:
            return 0.0
        
        return next_patterns.get(to_pattern, 0) / total


class MarkovChainPredictor:
    """Position-based Markov chain for number prediction"""
    
    def __init__(self, lottery_config: LotteryConfig):
        """
        Initialize Markov chain predictor
        
        Args:
            lottery_config: Lottery configuration
        """
        self.config = lottery_config
        
        # Transition matrices for each position
        # transitions[position][from_number][to_number] = count
        self.transitions = [
            defaultdict(lambda: defaultdict(int))
            for _ in range(self.config.main_count)
        ]
    
    def build_from_draws(
        self,
        draws: List[Draw],
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ):
        """
        Build Markov chains from draw history
        
        Args:
            draws: List of draws (must be sorted)
            start_idx: Start index
            end_idx: End index
        """
        if end_idx is None:
            end_idx = len(draws) - 1
        
        # Clear existing transitions
        for trans in self.transitions:
            trans.clear()
        
        # Build transitions for each position
        for i in range(start_idx, min(end_idx, len(draws) - 1)):
            current_draw = draws[i]
            next_draw = draws[i + 1]
            
            # Sort numbers to ensure position consistency
            current_sorted = np.sort(current_draw.main_numbers)
            next_sorted = np.sort(next_draw.main_numbers)
            
            for pos in range(self.config.main_count):
                current_num = int(current_sorted[pos])
                next_num = int(next_sorted[pos])
                self.transitions[pos][current_num][next_num] += 1
    
    def predict_numbers(
        self,
        current_draw: Draw
    ) -> List[int]:
        """
        Predict next numbers using Markov chains
        
        Args:
            current_draw: Most recent draw
            
        Returns:
            List of predicted numbers
        """
        predicted = []
        current_sorted = np.sort(current_draw.main_numbers)
        
        for pos in range(self.config.main_count):
            current_num = int(current_sorted[pos])
            
            # Get transitions from current number at this position
            if current_num in self.transitions[pos] and self.transitions[pos][current_num]:
                next_nums = self.transitions[pos][current_num]
                # Pick most likely next number
                next_num = max(next_nums.items(), key=lambda x: x[1])[0]
                predicted.append(next_num)
            else:
                # No data, use frequency fallback or random
                predicted.append(current_num)  # Default to same number
        
        return predicted


if __name__ == '__main__':
    # Test state machine
    from config import get_lottery_config
    from models import Draw
    import numpy as np
    
    config = get_lottery_config('OPAP_JOKER')
    
    # Create test draws
    draws = [
        Draw("1", None, np.array([5, 12, 23, 34, 41]), np.array([10]), False),
        Draw("2", None, np.array([3, 12, 24, 35, 42]), np.array([15]), False),
        Draw("3", None, np.array([7, 13, 25, 36, 43]), np.array([8]), False),
        Draw("4", None, np.array([2, 14, 26, 37, 44]), np.array([12]), False),
    ]
    
    # Build state machine
    sm = StateMachine(config)
    sm.build_from_draws(draws)
    
    print("OE Transitions:")
    for from_pattern, to_patterns in sm.oe_transitions.items():
        print(f"  {from_pattern} -> {dict(to_patterns)}")
    
    # Predict next pattern
    current_oe = draws[-1].get_oe_pattern()
    predicted_oe = sm.predict_next_pattern(current_oe, 'OE', streak=0)
    print(f"\nCurrent OE: {current_oe}")
    print(f"Predicted next OE: {predicted_oe}")
    
    # Test Markov chain
    markov = MarkovChainPredictor(config)
    markov.build_from_draws(draws)
    
    predicted_numbers = markov.predict_numbers(draws[-1])
    print(f"\nPredicted numbers: {predicted_numbers}")