"""
Joker/Bonus number predictor with 4 independent methods and dynamic weighting
"""
from typing import List, Dict
import numpy as np
from collections import Counter, defaultdict

from models import Draw
from config import LotteryConfig


class JokerPredictor:
    """
    Independent bonus number prediction with 4 methods:
    1. Frequency Method - Most common bonus in window
    2. Avoid Recent Method - Least frequent non-recent bonus
    3. Markov Method - Sequence-based transition prediction
    4. Random Method - Truly random bonus selection
    
    Uses dynamic weighting based on recent performance.
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        """
        Initialize Joker predictor
        
        Args:
            lottery_config: Lottery configuration
        """
        self.config = lottery_config
        self.method_names = ['FREQUENCY', 'AVOID_RECENT', 'MARKOV', 'RANDOM']
        
        # Performance tracking for dynamic weighting
        self.method_performance: Dict[str, Dict[str, float]] = {
            method: {'success': 0, 'total': 0, 'accuracy': 0.0}
            for method in self.method_names
        }
        
        self.min_tests = 10  # Minimum tests before using performance-based weights
        self.lookback_recent = 5  # Recent draws to avoid
    
    def predict_frequency(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> List[int]:
        """
        Method 1: Most common Joker in window
        
        Args:
            draws: Historical draws
            start_idx: Start of window
            end_idx: End of window (inclusive)
            
        Returns:
            List of top frequent bonus numbers
        """
        # Count bonus frequencies in window
        bonus_freq = Counter()
        
        for i in range(start_idx, end_idx + 1):
            if i < len(draws):
                for bonus in draws[i].bonus_numbers:
                    bonus_freq[int(bonus)] += 1
        
        # Return top N most frequent
        count = self.config.bonus_play_count
        result = []
        
        if bonus_freq:
            for num, freq in bonus_freq.most_common(count):
                result.append(num)
        
        # Fill if needed
        while len(result) < count:
            rand = np.random.randint(1, self.config.bonus_pool + 1)
            if rand not in result:
                result.append(rand)
        
        return sorted(result[:count])
    
    def predict_avoid_recent(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> List[int]:
        """
        Method 2: Least frequent non-recent Joker
        
        Args:
            draws: Historical draws
            start_idx: Start of window
            end_idx: End of window (inclusive)
            
        Returns:
            List of least frequent non-recent bonus numbers
        """
        # Get recent bonuses to avoid
        recent_bonuses = set()
        recent_start = max(start_idx, end_idx - self.lookback_recent + 1)
        
        for i in range(recent_start, end_idx + 1):
            if i < len(draws):
                for bonus in draws[i].bonus_numbers:
                    recent_bonuses.add(int(bonus))
        
        # Count all frequencies
        frequency_counts = Counter()
        for i in range(start_idx, end_idx + 1):
            if i < len(draws):
                for bonus in draws[i].bonus_numbers:
                    frequency_counts[int(bonus)] += 1
        
        # Get candidates (not in recent)
        all_bonuses = set(range(1, self.config.bonus_pool + 1))
        candidate_bonuses = list(all_bonuses - recent_bonuses)
        
        # Return top N least frequent
        count = self.config.bonus_play_count
        result = []
        
        if candidate_bonuses:
            sorted_candidates = sorted(candidate_bonuses, key=lambda x: frequency_counts.get(x, 0))
            result = sorted_candidates[:count]
        
        # Fill if needed
        while len(result) < count:
            rand = np.random.randint(1, self.config.bonus_pool + 1)
            if rand not in result:
                result.append(rand)
        
        return sorted(result[:count])
    
    def predict_markov(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> List[int]:
        """
        Method 3: Markov chain prediction
        
        Args:
            draws: Historical draws
            start_idx: Start of window
            end_idx: End of window (inclusive)
            
        Returns:
            List of predicted bonus numbers based on transition probabilities
        """
        # Build transition matrix
        transitions = defaultdict(lambda: defaultdict(int))
        
        for i in range(start_idx, end_idx):
            if i < len(draws) - 1:
                for curr_bonus in draws[i].bonus_numbers:
                    for next_bonus in draws[i + 1].bonus_numbers:
                        transitions[int(curr_bonus)][int(next_bonus)] += 1
        
        # Get last bonus
        if end_idx < len(draws):
            last_bonuses = [int(b) for b in draws[end_idx].bonus_numbers]
        else:
            last_bonuses = [self.config.bonus_pool // 2]
        
        # Calculate next bonus probabilities
        next_bonus_probs = defaultdict(float)
        
        for last_bonus in last_bonuses:
            if last_bonus in transitions:
                total_transitions = sum(transitions[last_bonus].values())
                if total_transitions > 0:
                    for next_bonus, count in transitions[last_bonus].items():
                        next_bonus_probs[next_bonus] += count / total_transitions
        
        # Return top N predicted
        count = self.config.bonus_play_count
        result = []
        
        if next_bonus_probs:
            sorted_probs = sorted(next_bonus_probs.items(), key=lambda x: x[1], reverse=True)
            result = [num for num, prob in sorted_probs[:count]]
        
        # Fill if needed
        while len(result) < count:
            rand = np.random.randint(1, self.config.bonus_pool + 1)
            if rand not in result:
                result.append(rand)
        
        return sorted(result[:count])
    
    def predict_random(self) -> List[int]:
        """
        Method 4: Purely random bonus selection
        
        Returns:
            List of random bonus numbers
        """
        count = self.config.bonus_play_count
        return sorted(np.random.choice(
            range(1, self.config.bonus_pool + 1),
            size=count,
            replace=False
        ).tolist())
    
    def predict_dynamic(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> List[int]:
        """
        Dynamic prediction using weighted voting
        
        Args:
            draws: Historical draws
            start_idx: Start of window
            end_idx: End of window (inclusive)
            
        Returns:
            List of predicted bonus numbers
        """
        # Get predictions from all methods
        predictions = {
            'FREQUENCY': self.predict_frequency(draws, start_idx, end_idx),
            'AVOID_RECENT': self.predict_avoid_recent(draws, start_idx, end_idx),
            'MARKOV': self.predict_markov(draws, start_idx, end_idx),
            'RANDOM': self.predict_random()
        }
        
        # Calculate weights
        weights = self._calculate_dynamic_weights()
        
        # Vote on individual numbers
        number_votes = defaultdict(float)
        for method, prediction in predictions.items():
            weight = weights[method]
            if isinstance(prediction, (list, tuple)):
                for num in prediction:
                    number_votes[int(num)] += weight
            else:
                number_votes[int(prediction)] += weight
        
        # Return top N by votes
        count = self.config.bonus_play_count
        if number_votes:
            sorted_nums = sorted(number_votes.items(), key=lambda x: x[1], reverse=True)
            return sorted([num for num, v in sorted_nums[:count]])
        
        # Fallback
        return self.predict_random()
    
    def _calculate_dynamic_weights(self) -> Dict[str, float]:
        """Calculate weights based on method performance"""
        weights = {}
        
        # Check if we have enough data
        total_tests = sum(self.method_performance[m]['total'] for m in self.method_names)
        
        if total_tests < self.min_tests:
            # Equal weights
            for method in self.method_names:
                weights[method] = 1.0 / len(self.method_names)
        else:
            # Performance-based weights
            accuracies = {
                method: self.method_performance[method]['accuracy']
                for method in self.method_names
            }
            
            total_accuracy = sum(accuracies.values())
            
            if total_accuracy > 0:
                for method in self.method_names:
                    weights[method] = accuracies[method] / total_accuracy
            else:
                for method in self.method_names:
                    weights[method] = 1.0 / len(self.method_names)
        
        return weights
    
    def update_performance(
        self,
        predictions: Dict[str, any],
        actual_bonus: int
    ):
        """
        Update performance tracking
        
        Args:
            predictions: Dictionary of method predictions
            actual_bonus: Actual bonus that occurred
        """
        for method, prediction in predictions.items():
            if method in self.method_performance:
                # Update total
                self.method_performance[method]['total'] += 1
                
                # Check if correct (handle lists)
                pred = predictions[method]
                if isinstance(pred, (list, tuple)):
                    is_correct = actual_bonus in pred
                else:
                    is_correct = pred == actual_bonus
                
                # Update success
                if is_correct:
                    self.method_performance[method]['success'] += 1
                
                # Update accuracy
                total = self.method_performance[method]['total']
                success = self.method_performance[method]['success']
                if total > 0:
                    accuracy = success / total
                    self.method_performance[method]['accuracy'] = accuracy