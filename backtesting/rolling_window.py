"""
Rolling window backtesting engine for multi-strategy evaluation
"""
from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np

from models import Draw, Prediction
from strategies.base_strategy import BaseStrategy
from predictors.joker_predictor import JokerPredictor
from config import LotteryConfig, BacktestConfig


class RollingWindowBacktester:
    """
    Multi-strategy rolling window backtesting
    
    Tests multiple strategies simultaneously on same data windows.
    Tracks performance metrics for ranking and selection.
    """
    
    def __init__(
        self,
        lottery_config: LotteryConfig,
        backtest_config: BacktestConfig
    ):
        """
        Initialize backtester
        
        Args:
            lottery_config: Lottery configuration
            backtest_config: Backtest parameters
        """
        self.lottery_config = lottery_config
        self.backtest_config = backtest_config
        self.strategies: List[BaseStrategy] = []
        self.joker_predictor = JokerPredictor(lottery_config)
    
    def add_strategy(self, strategy: BaseStrategy):
        """Add a strategy to test"""
        self.strategies.append(strategy)
    

    def calculate_calibrated_confidence(
        self,
        strategy_results: Dict[str, List],
        window_count: int = 50
    ) -> float:
        """
        Calculate confidence based on actual recent performance.
        
        Uses the last N windows to determine how well the strategy
        actually performed, not arbitrary self-assessment.
        
        Args:
            strategy_results: Results from backtesting
            window_count: Number of recent windows to analyze (default 50)
            
        Returns:
            Calibrated confidence score (0-0.95)
        """
        if 'main_matches' not in strategy_results or not strategy_results['main_matches']:
            return 0.3  # Default low confidence if no data
        
        # Get recent results (last N windows)
        recent_matches = strategy_results['main_matches'][-window_count:]
        
        if not recent_matches:
            return 0.3
        
        # Calculate average performance
        avg_matches = np.mean(recent_matches)
        
        # Calculate random expectation
        random_expectation = (
            self.lottery_config.main_play_count * self.lottery_config.main_count
        ) / self.lottery_config.main_pool
        
        # Confidence = performance relative to random
        if random_expectation > 0:
            confidence = avg_matches / random_expectation
            # Normalize to 0-0.95 range
            # 1.0 = random (50% confidence)
            # 1.1 = 10% better (60% confidence)
            # 1.2 = 20% better (70% confidence)
            # 1.3 = 30% better (80% confidence)
            # 1.4+ = 40%+ better (90%+ confidence)
            
            if confidence < 0.9:
                calibrated = 0.3  # Worse than random
            elif confidence < 1.0:
                calibrated = 0.3 + (confidence - 0.9) * 2.0  # 0.3-0.5
            elif confidence < 1.1:
                calibrated = 0.5 + (confidence - 1.0) * 1.0  # 0.5-0.6
            elif confidence < 1.2:
                calibrated = 0.6 + (confidence - 1.1) * 1.0  # 0.6-0.7
            elif confidence < 1.3:
                calibrated = 0.7 + (confidence - 1.2) * 1.0  # 0.7-0.8
            else:
                calibrated = 0.8 + min((confidence - 1.3) * 0.75, 0.15)  # 0.8-0.95
            
            return min(calibrated, 0.95)
        
        return 0.5

    def run_backtest(
        self,
        draws: List[Draw],
        verbose: bool = True
    ) -> Dict[str, Dict[str, list]]:
        """
        Run backtest on all strategies
        
        Args:
            draws: List of historical draws
            verbose: Print progress messages
            
        Returns:
            Dictionary mapping strategy_id to performance metrics
        """
        window_size = self.backtest_config.window_size
        step_size = self.backtest_config.step_size
        
        # Initialize results storage
        results = {
            strategy.strategy_id: {
                'main_matches': [],
                'bonus_matches': [],
                'oe_correct': [],
                'hl_correct': [],
                'sum_correct': [],
                'confidence': [],
                'test_indices': []
            }
            for strategy in self.strategies
        }
        
        # Joker method tracking
        joker_method_results = {
            'FREQUENCY': [],
            'AVOID_RECENT': [],
            'MARKOV': [],
            'RANDOM': []
        }
        
        test_count = 0
        
        # Rolling window loop
        for window_start in range(0, len(draws) - window_size, step_size):
            window_end = window_start + window_size - 1
            test_idx = window_end + 1
            
            if test_idx >= len(draws):
                break
            
            test_count += 1
            
            if verbose and test_count % 10 == 0:
                print(f"  Test {test_count}: window [{window_start}:{window_end}], test {test_idx}")
            
            # Get actual test draw
            actual_draw = draws[test_idx]
            
            # Test each strategy
            for strategy in self.strategies:
                try:
                    # Get prediction
                    prediction = strategy.predict(draws, window_start, window_end)
                    
                    # Predict joker independently
                    predicted_bonuses = self.joker_predictor.predict_dynamic(
                        draws, window_start, window_end
                    )
                    prediction.bonus_numbers = predicted_bonuses
                    
                    # Evaluate prediction
                    evaluation = prediction.evaluate_against_draw(actual_draw)
                    
                    # Store results
                    results[strategy.strategy_id]['main_matches'].append(
                        evaluation['main_matches']
                    )
                    results[strategy.strategy_id]['bonus_matches'].append(
                        1 if evaluation['bonus_matches'] > 0 else 0
                    )
                    results[strategy.strategy_id]['oe_correct'].append(
                        1 if evaluation['oe_correct'] else 0
                    )
                    results[strategy.strategy_id]['hl_correct'].append(
                        1 if evaluation['hl_correct'] else 0
                    )
                    results[strategy.strategy_id]['sum_correct'].append(
                        1 if evaluation['sum_correct'] else 0
                    )
                    results[strategy.strategy_id]['confidence'].append(
                        prediction.confidence_score
                    )
                    results[strategy.strategy_id]['test_indices'].append(test_idx)
                    
                except Exception as e:
                    if verbose:
                        print(f"    Warning: {strategy.strategy_id} failed: {e}")
                    # Record zeros for failed prediction
                    results[strategy.strategy_id]['main_matches'].append(0)
                    results[strategy.strategy_id]['bonus_matches'].append(0)
                    results[strategy.strategy_id]['oe_correct'].append(0)
                    results[strategy.strategy_id]['hl_correct'].append(0)
                    results[strategy.strategy_id]['sum_correct'].append(0)
                    results[strategy.strategy_id]['confidence'].append(0.0)
                    results[strategy.strategy_id]['test_indices'].append(test_idx)
            
            # Test individual joker methods
            # Get actual bonus numbers (can be 1 or more)
            actual_bonuses = list(actual_draw.bonus_numbers) if len(actual_draw.bonus_numbers) > 0 else []
            
            joker_predictions = {
                'FREQUENCY': self.joker_predictor.predict_frequency(draws, window_start, window_end),
                'AVOID_RECENT': self.joker_predictor.predict_avoid_recent(draws, window_start, window_end),
                'MARKOV': self.joker_predictor.predict_markov(draws, window_start, window_end),
                'RANDOM': self.joker_predictor.predict_random()
            }
            
            for method, prediction in joker_predictions.items():
                # Check if any predicted bonus matches any actual bonus
                if isinstance(prediction, (list, tuple)):
                    matched = any(p in actual_bonuses for p in prediction)
                else:
                    matched = prediction in actual_bonuses
                joker_method_results[method].append(1 if matched else 0)
            
            # Update joker predictor performance
            # Update performance (using first actual bonus for compatibility)
            first_actual = actual_bonuses[0] if actual_bonuses else 0
            self.joker_predictor.update_performance(joker_predictions, first_actual)
        
        if verbose:
            print(f"\nBacktest complete: {test_count} tests performed")
        
        # Add joker method results
        results['_JOKER_METHODS'] = joker_method_results
        
        return results
    
    def calculate_summary_metrics(
        self,
        results: Dict[str, Dict[str, list]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate summary statistics from backtest results
        
        Args:
            results: Raw backtest results
            
        Returns:
            Summary metrics for each strategy
        """
        summaries = {}
        
        for strategy_id, strategy_results in results.items():
            if strategy_id == '_JOKER_METHODS':
                continue
            
            if not strategy_results['main_matches']:
                continue
            
            # Calculate averages
            avg_main_matches = np.mean(strategy_results['main_matches'])
            joker_accuracy = np.mean(strategy_results['bonus_matches'])
            oe_accuracy = np.mean(strategy_results['oe_correct'])
            hl_accuracy = np.mean(strategy_results['hl_correct'])
            sum_accuracy = np.mean(strategy_results['sum_correct'])
            avg_confidence = np.mean(strategy_results['confidence'])
            
            # Calculate composite score
            # Random expectation for main matches
            random_expectation = (
                self.lottery_config.main_play_count * self.lottery_config.main_count
            ) / self.lottery_config.main_pool
            
            # Normalize main matches
            normalized_main = avg_main_matches / random_expectation if random_expectation > 0 else 0
            
            # Normalize joker (random = 1/pool)
            random_joker = 1.0 / self.lottery_config.bonus_pool
            normalized_joker = min(joker_accuracy / random_joker, 1.0) if random_joker > 0 else 0
            
            # Pattern accuracy
            pattern_accuracy = (oe_accuracy + hl_accuracy) / 2
            
            # Composite score (weighted combination)
            composite = (
                normalized_joker * 0.4 +
                normalized_main * 0.3 +
                pattern_accuracy * 0.3
            )
            
            # Scale to 0-100
            composite_score = composite * 100
            
            # Calculate calibrated confidence from actual performance
            calibrated_confidence = self.calculate_calibrated_confidence(strategy_results, window_count=50)
            
            summaries[strategy_id] = {
                'avg_main_matches': avg_main_matches,
                'joker_accuracy': joker_accuracy,
                'oe_accuracy': oe_accuracy,
                'hl_accuracy': hl_accuracy,
                'sum_accuracy': sum_accuracy,
                'pattern_accuracy': pattern_accuracy,
                'avg_confidence': avg_confidence,  # Keep original for comparison
                'calibrated_confidence': calibrated_confidence,  # NEW: Actual accuracy
                'composite_score': composite_score,
                'test_count': len(strategy_results['main_matches'])
            }
        
        # Add joker methods summary
        if '_JOKER_METHODS' in results:
            joker_summaries = {}
            for method, method_results in results['_JOKER_METHODS'].items():
                if method_results:
                    joker_summaries[method] = {
                        'accuracy': np.mean(method_results),
                        'test_count': len(method_results)
                    }
            summaries['_JOKER_METHODS'] = joker_summaries
        
        return summaries
    
    def rank_strategies(
        self,
        summaries: Dict[str, Dict[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        Rank strategies by main matches (what actually wins prizes!)
        
        Args:
            summaries: Summary metrics
            
        Returns:
            List of (strategy_id, avg_main_matches) tuples, sorted descending
        """
        rankings = []
        
        for strategy_id, metrics in summaries.items():
            if strategy_id == '_JOKER_METHODS':
                continue
            
            # Rank by main matches instead of composite score
            if 'avg_main_matches' in metrics:
                rankings.append((strategy_id, metrics['avg_main_matches']))
        
        rankings.sort(key=lambda x: -x[1])
        
        return rankings


if __name__ == '__main__':
    # Test the backtester
    from config import get_lottery_config, get_backtest_config
    from strategies.strat01_state_frequency import Strategy01_StatePatternFreq
    from strategies.strat02_pure_frequency import Strategy02_PureFrequency
    from models import Draw
    import numpy as np
    
    lottery_config = get_lottery_config('OPAP_JOKER')
    backtest_config = get_backtest_config()
    
    # Create test draws
    draws = [
        Draw(str(i), None,
             np.random.choice(range(1, 46), size=5, replace=False),
             np.array([np.random.randint(1, 21)]),
             False)
        for i in range(200)
    ]
    
    # Initialize backtester
    backtester = RollingWindowBacktester(lottery_config, backtest_config)
    
    # Add strategies
    backtester.add_strategy(Strategy01_StatePatternFreq(lottery_config))
    backtester.add_strategy(Strategy02_PureFrequency(lottery_config))
    
    # Run backtest
    print("Running backtest...")
    results = backtester.run_backtest(draws, verbose=True)
    
    # Calculate summaries
    summaries = backtester.calculate_summary_metrics(results)
    
    # Display results
    print("\n=== BACKTEST RESULTS ===")
    for strategy_id, metrics in summaries.items():
        if strategy_id != '_JOKER_METHODS':
            print(f"\n{strategy_id}:")
            print(f"  Avg Main Matches: {metrics['avg_main_matches']:.3f}")
            print(f"  Joker Accuracy: {metrics['joker_accuracy']:.2%}")
            print(f"  OE Accuracy: {metrics['oe_accuracy']:.2%}")
            print(f"  HL Accuracy: {metrics['hl_accuracy']:.2%}")
            print(f"  Composite Score: {metrics['composite_score']:.1f}")
    
    # Rankings
    rankings = backtester.rank_strategies(summaries)
    print("\n=== STRATEGY RANKINGS ===")
    for rank, (strategy_id, score) in enumerate(rankings, 1):
        print(f"{rank}. {strategy_id}: {score:.1f}")