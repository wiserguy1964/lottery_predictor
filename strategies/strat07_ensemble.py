"""
Strategy 07: Adaptive Ensemble Strategy
Dynamic weighting of top-performing strategies
"""
from typing import List, Dict
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from config import LotteryConfig


class Strategy07_AdaptiveEnsemble(BaseStrategy):
    """
    Adaptive Ensemble Strategy
    
    Dynamically weights predictions from multiple strategies based on
    their recent performance. Uses weighted voting for final prediction.
    """
    
    def __init__(self, lottery_config: LotteryConfig, base_strategies: List[BaseStrategy] = None):
        super().__init__(lottery_config, "STRAT07", "Adaptive Ensemble Strategy")
        
        # Store base strategies
        self.base_strategies = base_strategies if base_strategies else []
        
        # Performance tracking for each strategy
        self.strategy_performance: Dict[str, Dict[str, float]] = {}
        for strategy in self.base_strategies:
            self.strategy_performance[strategy.strategy_id] = {
                'main_matches': [],
                'joker_matches': [],
                'oe_matches': [],
                'hl_matches': [],
                'confidence': []
            }
    
    def add_strategy(self, strategy: BaseStrategy):
        """Add a strategy to the ensemble"""
        if strategy.strategy_id not in [s.strategy_id for s in self.base_strategies]:
            self.base_strategies.append(strategy)
            self.strategy_performance[strategy.strategy_id] = {
                'main_matches': [],
                'joker_matches': [],
                'oe_matches': [],
                'hl_matches': [],
                'confidence': []
            }
    
    def predict(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> Prediction:
        """Generate ensemble prediction using weighted voting"""
        
        if not self.base_strategies:
            # No strategies available, return default
            return Prediction(
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                main_numbers=list(range(1, self.config.main_play_count + 1)),
                bonus_numbers=[self.config.bonus_pool // 2],
                predicted_oe="2O3E",
                predicted_hl="3L2H",
                predicted_sum_bracket="100-119",
                confidence_score=0.3
            )
        
        # Get predictions from all base strategies
        predictions = []
        for strategy in self.base_strategies:
            try:
                pred = strategy.predict(draws, start_idx, end_idx)
                predictions.append(pred)
            except Exception as e:
                print(f"Warning: Strategy {strategy.strategy_id} failed: {e}")
                continue
        
        if not predictions:
            # All strategies failed
            return Prediction(
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                main_numbers=list(range(1, self.config.main_play_count + 1)),
                bonus_numbers=[self.config.bonus_pool // 2],
                predicted_oe="2O3E",
                predicted_hl="3L2H",
                predicted_sum_bracket="100-119",
                confidence_score=0.3
            )
        
        # Calculate weights for each strategy
        weights = self._calculate_weights()
        
        # Weighted voting for main numbers
        main_numbers = self._weighted_number_vote(predictions, weights)
        
        # Weighted voting for bonus numbers
        bonus_numbers = self._weighted_number_vote(predictions, weights, is_bonus=True)
        
        # Weighted voting for patterns
        predicted_oe = self._weighted_pattern_vote(
            [p.predicted_oe for p in predictions],
            [weights.get(p.strategy_id, 0.0) for p in predictions]
        )
        
        predicted_hl = self._weighted_pattern_vote(
            [p.predicted_hl for p in predictions],
            [weights.get(p.strategy_id, 0.0) for p in predictions]
        )
        
        predicted_sum = self._weighted_pattern_vote(
            [p.predicted_sum_bracket for p in predictions],
            [weights.get(p.strategy_id, 0.0) for p in predictions]
        )
        
        # Average confidence weighted by strategy weights
        confidence = sum(
            pred.confidence_score * weights.get(pred.strategy_id, 0.0)
            for pred in predictions
        )
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=sorted(main_numbers),
            bonus_numbers=bonus_numbers,
            predicted_oe=predicted_oe,
            predicted_hl=predicted_hl,
            predicted_sum_bracket=predicted_sum,
            confidence_score=confidence,
            metadata={
                'base_strategies': [s.strategy_id for s in self.base_strategies],
                'weights': weights
            }
        )
    
    def _calculate_weights(self) -> Dict[str, float]:
        """
        Calculate weights for each strategy based on performance
        
        Returns:
            Dictionary of strategy_id -> weight
        """
        weights = {}
        
        for strategy in self.base_strategies:
            strategy_id = strategy.strategy_id
            perf = self.strategy_performance.get(strategy_id, {})
            
            # Check if we have performance data
            if not perf.get('confidence'):
                # No performance data, use strategy's own confidence
                weights[strategy_id] = 0.5
                continue
            
            # Calculate composite score from recent performance
            recent_window = min(20, len(perf.get('main_matches', [])))
            
            if recent_window == 0:
                weights[strategy_id] = 0.5
                continue
            
            # Get recent metrics
            recent_main = perf['main_matches'][-recent_window:]
            recent_joker = perf['joker_matches'][-recent_window:]
            recent_oe = perf['oe_matches'][-recent_window:]
            recent_hl = perf['hl_matches'][-recent_window:]
            recent_conf = perf['confidence'][-recent_window:]
            
            # Calculate averages
            avg_main = np.mean(recent_main) if recent_main else 0
            avg_joker = np.mean(recent_joker) if recent_joker else 0
            avg_oe = np.mean(recent_oe) if recent_oe else 0
            avg_hl = np.mean(recent_hl) if recent_hl else 0
            avg_conf = np.mean(recent_conf) if recent_conf else 0.5
            
            # Composite score (weighted)
            composite = (
                avg_joker * 0.4 +  # Joker accuracy is important
                avg_main * 0.3 +   # Main number matches
                avg_oe * 0.15 +    # OE pattern accuracy
                avg_hl * 0.15      # HL pattern accuracy
            )
            
            # Incorporate confidence
            score = composite * avg_conf
            
            weights[strategy_id] = max(0.1, min(0.9, score))
        
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            for sid in weights:
                weights[sid] /= total
        
        return weights
    
    def _weighted_number_vote(
        self,
        predictions: List[Prediction],
        weights: Dict[str, float],
        is_bonus: bool = False
    ) -> List[int]:
        """
        Weighted voting for number selection
        
        Args:
            predictions: List of predictions
            weights: Strategy weights
            is_bonus: If True, vote on bonus numbers; else main numbers
            
        Returns:
            List of selected numbers
        """
        # Count weighted votes for each number
        votes = {}
        pool_size = self.config.bonus_pool if is_bonus else self.config.main_pool
        
        for i in range(1, pool_size + 1):
            votes[i] = 0.0
        
        # Add weighted votes
        for pred in predictions:
            weight = weights.get(pred.strategy_id, 0.0)
            numbers = pred.bonus_numbers if is_bonus else pred.main_numbers
            
            for num in numbers:
                if num in votes:
                    votes[num] += weight
        
        # Select top numbers
        count = self.config.bonus_play_count if is_bonus else self.config.main_play_count
        sorted_numbers = sorted(votes.items(), key=lambda x: -x[1])
        selected = [num for num, vote in sorted_numbers[:count]]
        
        return sorted(selected)
    
    def _weighted_pattern_vote(
        self,
        patterns: List[str],
        weights: List[float]
    ) -> str:
        """
        Weighted voting for pattern selection
        
        Args:
            patterns: List of pattern strings
            weights: Corresponding weights
            
        Returns:
            Most voted pattern
        """
        pattern_votes = {}
        
        for pattern, weight in zip(patterns, weights):
            if pattern in pattern_votes:
                pattern_votes[pattern] += weight
            else:
                pattern_votes[pattern] = weight
        
        if not pattern_votes:
            return "2O3E"  # Default
        
        return max(pattern_votes.items(), key=lambda x: x[1])[0]
    
    def update_performance(
        self,
        strategy_id: str,
        main_matches: float,
        joker_correct: bool,
        oe_correct: bool,
        hl_correct: bool,
        confidence: float
    ):
        """Update performance metrics for a strategy"""
        if strategy_id not in self.strategy_performance:
            return
        
        perf = self.strategy_performance[strategy_id]
        perf['main_matches'].append(main_matches)
        perf['joker_matches'].append(1.0 if joker_correct else 0.0)
        perf['oe_matches'].append(1.0 if oe_correct else 0.0)
        perf['hl_matches'].append(1.0 if hl_correct else 0.0)
        perf['confidence'].append(confidence)
        
        # Keep only recent history (last 50 entries)
        for key in perf:
            if len(perf[key]) > 50:
                perf[key] = perf[key][-50:]
    
    def calculate_confidence(
        self,
        draws: List[Draw],
        start_idx: int,
        end_idx: int
    ) -> float:
        """Confidence is average of base strategy confidences"""
        if not self.base_strategies:
            return 0.5
        
        confidences = [
            s.calculate_confidence(draws, start_idx, end_idx)
            for s in self.base_strategies
        ]
        
        return np.mean(confidences)