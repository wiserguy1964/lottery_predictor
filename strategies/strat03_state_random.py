"""
Strategy 03: State Patterns + Random
Uses pattern prediction with random number selection within constraints
"""
from typing import List
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction, parse_sum_bracket
from analyzers.frequency_analyzer import PatternAnalyzer
from analyzers.state_machine import StateMachine
from config import LotteryConfig


class Strategy03_StatePatternRandom(BaseStrategy):
    """
    State Patterns + Random Strategy
    
    Predicts patterns using state machines but selects numbers randomly
    while matching the predicted pattern constraints.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(lottery_config, "STRAT03", "State Patterns + Random")
        self.state_machine = StateMachine(lottery_config)
        self.pattern_analyzer = PatternAnalyzer(lottery_config)
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate prediction using state patterns with random selection"""
        
        # 1. Build state machines
        self.state_machine.build_from_draws(draws, start_idx, end_idx)
        
        # 2. Get current patterns
        current_draw = draws[end_idx]
        current_oe = current_draw.get_oe_pattern(self.config.main_pool)
        current_hl = current_draw.get_hl_pattern(self.config.main_pool)
        
        # 3. Calculate streaks
        oe_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'OE')
        hl_streak = self.pattern_analyzer.calculate_streak(draws, end_idx, 'HL')
        
        # 4. Predict next patterns
        predicted_oe = self.state_machine.predict_next_pattern(current_oe, 'OE', oe_streak)
        predicted_hl = self.state_machine.predict_next_pattern(current_hl, 'HL', hl_streak)
        predicted_sum = current_draw.get_sum_bracket()  # Use current sum
        
        # 5. Generate random numbers matching patterns
        main_numbers = self._generate_random_by_pattern(
            predicted_oe,
            predicted_hl,
            self.config.main_play_count
        )
        
        # 6. Predict bonus
        bonus_numbers = [self.config.bonus_pool // 2]
        
        # 7. Calculate confidence (capped for random strategies)
        confidence = min(0.7, self.calculate_confidence(draws, start_idx, end_idx))
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,
            predicted_hl=predicted_hl,
            predicted_sum_bracket=predicted_sum,
            confidence_score=confidence
        )
    
    def _generate_random_by_pattern(
        self,
        target_oe: str,
        target_hl: str,
        count: int
    ) -> List[int]:
        """Generate random numbers matching pattern constraints"""
        
        # Parse patterns
        odd_target = int(target_oe[0])
        low_target = int(target_hl[0])
        threshold = self.config.main_pool // 2
        
        # Categorize all numbers
        odd_low = [n for n in range(1, self.config.main_pool + 1) 
                   if n % 2 == 1 and n <= threshold]
        odd_high = [n for n in range(1, self.config.main_pool + 1) 
                    if n % 2 == 1 and n > threshold]
        even_low = [n for n in range(1, self.config.main_pool + 1) 
                    if n % 2 == 0 and n <= threshold]
        even_high = [n for n in range(1, self.config.main_pool + 1) 
                     if n % 2 == 0 and n > threshold]
        
        # Calculate needed from each group
        # GroupA (OddLow) + GroupB (OddHigh) = odd_target
        # GroupC (EvenLow) + GroupD (EvenHigh) = even_target
        # GroupA + GroupC = low_target
        group_a = min(odd_target, low_target)
        group_b = odd_target - group_a
        group_c = low_target - group_a
        group_d = count - (group_a + group_b + group_c)
        
        # Ensure non-negative
        group_a = max(0, group_a)
        group_b = max(0, group_b)
        group_c = max(0, group_c)
        group_d = max(0, group_d)
        
        # Randomly select from each group
        selected = []
        
        if group_a > 0 and len(odd_low) > 0:
            selected.extend(np.random.choice(odd_low, min(group_a, len(odd_low)), replace=False))
        
        if group_b > 0 and len(odd_high) > 0:
            selected.extend(np.random.choice(odd_high, min(group_b, len(odd_high)), replace=False))
        
        if group_c > 0 and len(even_low) > 0:
            selected.extend(np.random.choice(even_low, min(group_c, len(even_low)), replace=False))
        
        if group_d > 0 and len(even_high) > 0:
            selected.extend(np.random.choice(even_high, min(group_d, len(even_high)), replace=False))
        
        # Fill any remaining slots with random numbers
        all_numbers = list(range(1, self.config.main_pool + 1))
        while len(selected) < count:
            num = np.random.choice(all_numbers)
            if num not in selected:
                selected.append(num)
        
        return sorted(selected[:count])
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> float:
        """Confidence for random strategy (moderate)"""
        return 0.5  # Fixed moderate confidence for random selection