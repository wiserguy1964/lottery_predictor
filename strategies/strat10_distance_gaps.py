"""
Strategy 10: Distance Gaps Pattern Analysis
Advanced temporal gap-distance scoring using statistical deviation

This strategy analyzes the temporal dynamics of number appearances by:
1. Tracking "gaps" (draws since last appearance) for each number
2. Computing distance from collective gap statistics (mean/median)
3. Building frequency distributions of historical distance patterns
4. Scoring numbers whose current distance matches high-frequency patterns

Note: For educational/experimental use only. Lottery draws are random events.
"""

from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np

from strategies.base_strategy import BaseStrategy
from models import Draw, Prediction
from config import LotteryConfig


class DistanceGapsCalculator:
    """
    Core engine for gap-distance pattern analysis.
    
    Analyzes how far each number's current gap deviates from the 
    statistical norm (mean/median) of all gaps, and scores numbers
    based on historical frequency of similar deviations.
    """
    
    def __init__(self, lottery_config: LotteryConfig, bin_size: int = 5, threshold: int = 9):
        """
        Initialize calculator
        
        Args:
            lottery_config: Lottery configuration
            bin_size: Size of number bins for grouping (e.g., 5 = bins 1-5, 6-10, etc.)
            threshold: Only analyze gaps within this many draws from the end
        """
        self.config = lottery_config
        self.game_max_size = lottery_config.main_pool
        self.draw_size = lottery_config.main_count
        self.BIN_SIZE = bin_size
        self.THRESHOLD = threshold

    def calculate_distance_gaps(self, draws: List[Draw], start_idx: int, end_idx: int,
                                statistic_func=np.mean) -> Tuple[Dict, Dict]:
        """
        Calculate frequency of distances of each number's gaps from a statistic.
        
        Args:
            draws: List of draws
            start_idx: Start index for analysis
            end_idx: End index for analysis
            statistic_func: Function to calculate statistic (mean, median, etc.)
            
        Returns:
            - distance_frequencies: Dict of number -> {positive/negative -> {distance -> freq}}
            - current_gaps: Dict of number -> current gap
        """
        distance_frequencies = defaultdict(lambda: {"positive": defaultdict(int), "negative": defaultdict(int)})
        current_gaps = {num: 0 for num in range(1, self.game_max_size + 1)}
        
        # Get total draws in history for threshold calculation
        total_draws = end_idx - start_idx + 1
        
        # Iterate from oldest to newest
        for i, draw_idx in enumerate(range(start_idx, end_idx + 1)):
            if draw_idx < len(draws):
                draw_numbers = set(draws[draw_idx].main_numbers)
                
                # Update gaps
                for num in range(1, self.game_max_size + 1):
                    if num in draw_numbers:
                        current_gaps[num] = 0
                    else:
                        current_gaps[num] += 1
                
                # Only calculate distances in recent threshold window
                if total_draws - i <= self.THRESHOLD:
                    gap_values = list(current_gaps.values())
                    if gap_values:
                        statistic_value = round(statistic_func(gap_values))
                        
                        for num, gap in current_gaps.items():
                            distance = gap - statistic_value
                            if distance > 0:
                                distance_frequencies[num]["positive"][int(distance)] += 1
                            elif distance < 0:
                                distance_frequencies[num]["negative"][int(abs(distance))] += 1
                            else:
                                distance_frequencies[num]["negative"][0] += 1

        return dict(distance_frequencies), current_gaps
    
    def distribute_to_bins(self, distance_frequencies: Dict) -> Dict:
        """
        Distribute distances into bins based on number ranges.
        
        Args:
            distance_frequencies: Output from calculate_distance_gaps
            
        Returns:
            Binned distances by number group
        """
        binned_distances = defaultdict(lambda: defaultdict(lambda: {"positive": defaultdict(int), "negative": defaultdict(int)}))

        for num in distance_frequencies:
            bin_num = (num - 1) // self.BIN_SIZE + 1
            for category in ["positive", "negative"]:
                for distance, freq in distance_frequencies[num][category].items():
                    binned_distances[bin_num][num][category][distance] += freq

        return dict(binned_distances)

    def calculate_latest_distances(self, current_gaps: Dict, statistic_func=np.mean) -> Dict:
        """
        Calculate latest distances for each number based on current gaps.
        
        Args:
            current_gaps: Current gap for each number
            statistic_func: Function to calculate statistic
            
        Returns:
            Dictionary of number -> {positive: distance, negative: distance}
        """
        latest_distances = defaultdict(lambda: {"positive": 0, "negative": 0})
        gap_values = list(current_gaps.values())
        
        if gap_values:
            statistic_value = statistic_func(gap_values)
            for num, gap in current_gaps.items():
                distance = gap - statistic_value
                if distance > 0:
                    latest_distances[num]["positive"] = int(distance)
                elif distance < 0:
                    latest_distances[num]["negative"] = int(abs(distance))
                else:
                    latest_distances[num]["negative"] = 0

        return dict(latest_distances)

    def calculate_scores(self, binned_distances: Dict, latest_distances: Dict,
                        current_gaps: Dict) -> List[List]:
        """
        Calculate scores based on gap distance pattern matching.
        
        Args:
            binned_distances: Binned distance frequencies
            latest_distances: Current distances from statistic
            current_gaps: Current gaps for each number
            
        Returns:
            List of [number, score, current_gap, current_distance] sorted by score
        """
        scores = [[num, 0, current_gaps.get(num, 0), 0] for num in range(1, self.game_max_size + 1)]

        for num in range(1, self.game_max_size + 1):
            try:
                bin_num = (num - 1) // self.BIN_SIZE + 1
                bin_data = binned_distances.get(bin_num, {})

                if num in bin_data:
                    current_distance = latest_distances[num]["positive"] or latest_distances[num]["negative"]
                    scores[num - 1][3] = current_distance

                    if latest_distances[num]["positive"] != 0:
                        latest_distance = latest_distances[num]["positive"]
                        section = "positive"
                    else:
                        latest_distance = latest_distances[num]["negative"]
                        section = "negative"

                    if latest_distance in bin_data[num].get(section, {}):
                        latest_freq = bin_data[num][section][latest_distance]
                        
                        # Count matching frequencies across bin
                        same_freq_count = sum(
                            1 for bn in bin_data
                            for freq in bin_data[bn].get(section, {}).values()
                            if freq == latest_freq
                        )
                        
                        # Score if multiple distances share same frequency OR highest frequency
                        if same_freq_count > 1:
                            scores[num - 1][1] += 100
                        elif latest_freq == max(bin_data[num][section].values(), default=0):
                            scores[num - 1][1] += 100

            except Exception:
                # Silently continue on errors
                continue

        # Normalize scores to 0-100
        max_score = max(score[1] for score in scores)
        if max_score > 0:
            for entry in scores:
                entry[1] = round((entry[1] / max_score) * 100, 2)

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
    
    def calculate_combined_scores(self, statistics_results: Dict[str, Dict]) -> List[List]:
        """
        Combine scores from multiple statistics (mean + median).
        
        Args:
            statistics_results: Dict of statistic_name -> {scores, current_gaps, latest_distances}
            
        Returns:
            Combined scores with multiplier for consensus
        """
        combined_scores = [[num, 0, 0, 0] for num in range(1, self.game_max_size + 1)]
        
        # Extract scores by statistic
        all_stat_scores = {}
        for stat_name, results in statistics_results.items():
            all_stat_scores[stat_name] = {score[0]: score[1] for score in results['scores']}
        
        # Combine with multiplier for consensus
        for i in range(len(combined_scores)):
            number = i + 1
            mean_score = all_stat_scores.get('mean', {}).get(number, 0)
            median_score = all_stat_scores.get('median', {}).get(number, 0)
            
            scoring_stats = [s for s, sc in [('mean', mean_score), ('median', median_score)] if sc > 0]
            stat_count = len(scoring_stats)
            
            if stat_count > 0:
                combined_scores[i][1] = 100 * stat_count  # Multiplier for consensus
                # Pull gap/distance from mean results
                if 'mean' in statistics_results:
                    for se in statistics_results['mean']['scores']:
                        if se[0] == number:
                            combined_scores[i][2] = se[2]  # current gap
                            combined_scores[i][3] = se[3]  # current distance
                            break
        
        # Normalize
        max_score = max(score[1] for score in combined_scores)
        if max_score > 0:
            for entry in combined_scores:
                entry[1] = round((entry[1] / max_score) * 100, 2)
        
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        return combined_scores


class Strategy10_DistanceGaps(BaseStrategy):
    """
    STRAT10: Distance Gaps Pattern Strategy
    
    Implements advanced temporal gap analysis for lottery prediction.
    Combines mean and median gap statistics for robust scoring.
    """

    def __init__(self, lottery_config: LotteryConfig, bin_size: int = 5, threshold: int = 9):
        """
        Initialize strategy
        
        Args:
            lottery_config: Lottery configuration
            bin_size: Size of number bins (default: 5)
            threshold: Recent draws to analyze (default: 9)
        """
        super().__init__(lottery_config, "STRAT10", "Distance Gaps Analysis")
        self.bin_size = bin_size
        self.threshold = threshold
        self.calculator = DistanceGapsCalculator(lottery_config, bin_size, threshold)

    def predict(self, draws: List[Draw], start_idx: int, end_idx: int) -> Prediction:
        """
        Generate prediction using gap-distance pattern analysis.
        
        Args:
            draws: List of Draw objects
            start_idx: Starting index for analysis window
            end_idx: Ending index for analysis window
            
        Returns:
            Prediction object with top-scoring numbers
        """
        # Ensure we have enough data
        window_size = end_idx - start_idx + 1
        if window_size < self.threshold:
            # Fallback to random selection
            return self._fallback_prediction(draws, end_idx, 
                                           metadata={'note': 'Insufficient data', 
                                                    'window_size': window_size})
        
        try:
            # Calculate for both mean and median statistics
            statistics_results = {}
            
            for stat_name, stat_func in [('mean', np.mean), ('median', np.median)]:
                dist_freq, curr_gaps = self.calculator.calculate_distance_gaps(
                    draws, start_idx, end_idx, stat_func
                )
                binned = self.calculator.distribute_to_bins(dist_freq)
                latest = self.calculator.calculate_latest_distances(curr_gaps, stat_func)
                scores = self.calculator.calculate_scores(binned, latest, curr_gaps)
                
                statistics_results[stat_name] = {
                    'scores': scores,
                    'current_gaps': curr_gaps,
                    'latest_distances': latest
                }
            
            # Combine results from both statistics
            combined_scores = self.calculator.calculate_combined_scores(statistics_results)
            
            # Extract top predictions (prefer scored numbers)
            scored_numbers = [entry for entry in combined_scores if entry[1] > 0]
            if not scored_numbers:
                scored_numbers = combined_scores  # Fallback to all numbers
            
            # Select top N numbers
            main_numbers = [entry[0] for entry in scored_numbers[:self.config.main_play_count]]
            
            # Ensure we have enough unique numbers
            if len(main_numbers) < self.config.main_play_count:
                remaining = self.config.main_play_count - len(main_numbers)
                available = [n for n in range(1, self.config.main_pool + 1) if n not in main_numbers]
                main_numbers.extend(list(np.random.choice(available, size=remaining, replace=False)))
            
            main_numbers = sorted(main_numbers)
            
            # FIXED: Predict patterns based on selected numbers (not copying last draw)
            num_odd = sum(1 for n in main_numbers if n % 2 == 1)
            num_even = len(main_numbers) - num_odd
            predicted_oe = f"{num_odd}O{num_even}E"
            
            mid_point = self.config.main_pool // 2
            num_low = sum(1 for n in main_numbers if n <= mid_point)
            num_high = len(main_numbers) - num_low
            predicted_hl = f"{num_low}L{num_high}H"
            
            total_sum = sum(main_numbers)
            bracket_start = (total_sum // 20) * 20
            predicted_sum_bracket = f"{bracket_start}-{bracket_start + 19}"
            
            # Predict bonus (placeholder - middle of range)
            bonus_numbers = [self.config.bonus_pool // 2]
            
            # Calculate confidence
            confidence = self.calculate_confidence(draws, start_idx, end_idx)
            
            return Prediction(
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                main_numbers=main_numbers,
                bonus_numbers=bonus_numbers,
                predicted_oe=predicted_oe,
                predicted_hl=predicted_hl,
                predicted_sum_bracket=predicted_sum_bracket,
                confidence_score=confidence,
                metadata={
                    'bin_size': self.bin_size,
                    'threshold': self.threshold,
                    'window_size': window_size,
                    'mean_top_5': [s[0] for s in statistics_results['mean']['scores'][:5]],
                    'median_top_5': [s[0] for s in statistics_results['median']['scores'][:5]],
                    'consensus_count': sum(1 for s in combined_scores if s[1] > 0)
                }
            )
            
        except Exception as e:
            # Graceful fallback to random selection
            return self._fallback_prediction(draws, end_idx, 
                                           metadata={'error': str(e), 'note': 'Error in calculation'})

    def _fallback_prediction(self, draws: List[Draw], end_idx: int, metadata: Dict) -> Prediction:
        """Helper method for fallback predictions"""
        main_numbers = list(np.random.choice(
            range(1, self.config.main_pool + 1),
            size=self.config.main_play_count,
            replace=False
        ))
        main_numbers.sort()
        
        # Predict patterns based on random numbers
        num_odd = sum(1 for n in main_numbers if n % 2 == 1)
        num_even = len(main_numbers) - num_odd
        predicted_oe = f"{num_odd}O{num_even}E"
        
        mid_point = self.config.main_pool // 2
        num_low = sum(1 for n in main_numbers if n <= mid_point)
        num_high = len(main_numbers) - num_low
        predicted_hl = f"{num_low}L{num_high}H"
        
        total_sum = sum(main_numbers)
        bracket_start = (total_sum // 20) * 20
        predicted_sum_bracket = f"{bracket_start}-{bracket_start + 19}"
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=main_numbers,
            bonus_numbers=[self.config.bonus_pool // 2],
            predicted_oe=predicted_oe,
            predicted_hl=predicted_hl,
            predicted_sum_bracket=predicted_sum_bracket,
            confidence_score=0.3,
            metadata=metadata
        )

    def calculate_confidence(self, draws: List[Draw], start_idx: int, end_idx: int) -> float:
        """
        Calculate confidence score based on data availability and score distribution.
        
        Higher confidence when:
        - More historical data available
        - Clear separation between high and low scored numbers
        
        Args:
            draws: List of Draw objects
            start_idx: Starting index for analysis window
            end_idx: Ending index for analysis window
            
        Returns:
            Confidence score between 0 and 1
        """
        window_size = end_idx - start_idx + 1
        
        # Base confidence from data volume
        if window_size < 30:
            base_confidence = 0.3
        elif window_size < 60:
            base_confidence = 0.5
        elif window_size < 90:
            base_confidence = 0.65
        else:
            base_confidence = 0.75
        
        # Try to calculate score separation (higher = more confident)
        try:
            # Get scores from mean statistic
            dist_freq, curr_gaps = self.calculator.calculate_distance_gaps(draws, start_idx, end_idx, np.mean)
            binned = self.calculator.distribute_to_bins(dist_freq)
            latest = self.calculator.calculate_latest_distances(curr_gaps, np.mean)
            scores = self.calculator.calculate_scores(binned, latest, curr_gaps)
            
            # Calculate score separation (top 5 vs bottom 5)
            if len(scores) >= 10:
                top_scores = [s[1] for s in scores[:5] if s[1] > 0]
                bottom_scores = [s[1] for s in scores[-5:]]
                
                if top_scores and bottom_scores:
                    top_avg = np.mean(top_scores)
                    bottom_avg = np.mean(bottom_scores)
                    
                    if top_avg > 0:
                        separation = (top_avg - bottom_avg) / top_avg
                        # Adjust confidence based on separation (0-0.25 range)
                        separation_bonus = min(separation * 0.25, 0.25)
                        base_confidence += separation_bonus
        except:
            pass  # Keep base confidence if calculation fails
        
        return min(base_confidence, 0.95)  # Cap at 0.95
