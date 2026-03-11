"""
Strategy 08: Multi-Signal Consensus

Uses multiple independent signals and only gives high confidence when they agree.

Signals:
1. Gap Analysis - Numbers overdue to appear
2. Sector Rotation - Which number ranges (sectors) are hot/cold
3. Pattern Momentum - Recent trend in OE/HL patterns
4. Frequency Cycles - Hot numbers with good gap timing
5. Sum Range Convergence - Sum patterns converging to mean

Confidence: Based on signal agreement (more signals agree = higher confidence)
"""

from typing import List, Tuple, Dict
import numpy as np
from collections import Counter, defaultdict

from models import Draw, Prediction
from strategies.base_strategy import BaseStrategy
from config import LotteryConfig


class Strategy08_MultiSignalConsensus(BaseStrategy):
    """
    Multi-signal strategy that combines 5 independent signals
    High confidence only when signals converge
    """
    
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(
            lottery_config,
            "STRAT08",
            "Multi-Signal Consensus"
        )
        # Define sectors (divide pool into 5 equal sectors)
        self.num_sectors = 5
        self.sector_size = lottery_config.main_pool // self.num_sectors
    
    def predict(self, draws: List[Draw], start_idx: int, end_idx: int) -> Prediction:
        """Generate prediction using multi-signal consensus"""
        
        # Collect signals
        signal_1 = self._signal_gap_analysis(draws, start_idx, end_idx)
        signal_2 = self._signal_sector_rotation(draws, start_idx, end_idx)
        signal_3 = self._signal_pattern_momentum(draws, start_idx, end_idx)
        signal_4 = self._signal_frequency_cycles(draws, start_idx, end_idx)
        signal_5 = self._signal_sum_convergence(draws, start_idx, end_idx)
        
        # Combine signals with voting
        all_signals = [signal_1, signal_2, signal_3, signal_4, signal_5]
        number_votes = Counter()
        
        for signal_numbers in all_signals:
            for num in signal_numbers:
                number_votes[num] += 1
        
        # Calculate consensus strength
        max_votes = max(number_votes.values())
        consensus_numbers = [num for num, votes in number_votes.items() if votes >= 3]
        
        # Select numbers prioritizing high consensus
        selected = []
        
        # First, take numbers with 4+ votes (strong consensus)
        for num, votes in sorted(number_votes.items(), key=lambda x: -x[1]):
            if votes >= 4 and len(selected) < self.config.main_play_count:
                selected.append(num)
        
        # Then 3 votes
        for num, votes in sorted(number_votes.items(), key=lambda x: -x[1]):
            if votes == 3 and num not in selected and len(selected) < self.config.main_play_count:
                selected.append(num)
        
        # Fill remaining with 2 votes
        for num, votes in sorted(number_votes.items(), key=lambda x: -x[1]):
            if votes == 2 and num not in selected and len(selected) < self.config.main_play_count:
                selected.append(num)
        
        # Fill with any remaining if needed
        if len(selected) < self.config.main_play_count:
            all_nums = set(range(1, self.config.main_pool + 1))
            remaining = list(all_nums - set(selected))
            np.random.shuffle(remaining)
            selected.extend(remaining[:self.config.main_play_count - len(selected)])
        
        main_numbers = sorted(selected[:self.config.main_play_count])
        
        # Calculate confidence based on consensus strength
        avg_votes = np.mean([number_votes[n] for n in main_numbers])
        confidence = self._calculate_consensus_confidence(avg_votes, number_votes, main_numbers)
        
        # Pattern predictions
        num_odd = sum(1 for n in main_numbers if n % 2 == 1)
        predicted_oe = f"{num_odd}O{self.config.main_play_count - num_odd}E"
        
        mid_point = self.config.main_pool // 2
        num_low = sum(1 for n in main_numbers if n <= mid_point)
        predicted_hl = f"{num_low}L{self.config.main_play_count - num_low}H"
        
        total = sum(main_numbers)
        predicted_sum = f"{(total // 20) * 20}-{(total // 20) * 20 + 19}"
        
        # Bonus
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
                'avg_votes': avg_votes,
                'max_votes': max_votes,
                'consensus_numbers': len([n for n in main_numbers if number_votes[n] >= 3])
            }
        )
    
    def _signal_gap_analysis(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[int]:
        """Signal 1: Numbers that are overdue (large gap since last appearance)"""
        
        # Track last appearance of each number
        last_seen = {}
        
        for i in range(start_idx, end_idx + 1):
            if i >= len(draws):
                break
            for num in draws[i].main_numbers:
                last_seen[int(num)] = i
        
        # Calculate gaps
        gaps = {}
        for num in range(1, self.config.main_pool + 1):
            if num in last_seen:
                gaps[num] = end_idx - last_seen[num]
            else:
                gaps[num] = end_idx - start_idx + 1  # Never seen
        
        # Return top numbers by gap (most overdue)
        sorted_gaps = sorted(gaps.items(), key=lambda x: -x[1])
        return [num for num, gap in sorted_gaps[:self.config.main_play_count * 2]]
    
    def _signal_sector_rotation(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[int]:
        """Signal 2: Identify which sectors are due based on rotation patterns"""
        
        # Count recent sector appearances
        sector_counts = Counter()
        recent_window = max(start_idx, end_idx - 20)
        
        for i in range(recent_window, end_idx + 1):
            if i >= len(draws):
                break
            for num in draws[i].main_numbers:
                sector = (int(num) - 1) // self.sector_size
                sector_counts[sector] += 1
        
        # Find coldest sectors (least represented)
        avg_count = np.mean(list(sector_counts.values())) if sector_counts else 0
        cold_sectors = [s for s in range(self.num_sectors) if sector_counts.get(s, 0) < avg_count]
        
        # Select numbers from cold sectors
        selected = []
        for sector in cold_sectors:
            sector_start = sector * self.sector_size + 1
            sector_end = min(sector_start + self.sector_size, self.config.main_pool + 1)
            selected.extend(range(sector_start, sector_end))
        
        return selected[:self.config.main_play_count * 2]
    
    def _signal_pattern_momentum(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[int]:
        """Signal 3: Follow recent OE/HL pattern trends"""
        
        # Analyze recent pattern trends
        recent_window = max(start_idx, end_idx - 10)
        oe_patterns = []
        hl_patterns = []
        
        for i in range(recent_window, end_idx + 1):
            if i >= len(draws):
                break
            draw = draws[i]
            num_odd = sum(1 for n in draw.main_numbers if n % 2 == 1)
            oe_patterns.append(num_odd)
            
            mid = self.config.main_pool // 2
            num_low = sum(1 for n in draw.main_numbers if n <= mid)
            hl_patterns.append(num_low)
        
        # Get trend (increasing/decreasing odd and low counts)
        target_odd = int(np.mean(oe_patterns)) if oe_patterns else self.config.main_play_count // 2
        target_low = int(np.mean(hl_patterns)) if hl_patterns else self.config.main_play_count // 2
        
        # Generate numbers matching this pattern
        mid_point = self.config.main_pool // 2
        
        odd_low = [n for n in range(1, self.config.main_pool + 1) if n % 2 == 1 and n <= mid_point]
        odd_high = [n for n in range(1, self.config.main_pool + 1) if n % 2 == 1 and n > mid_point]
        even_low = [n for n in range(1, self.config.main_pool + 1) if n % 2 == 0 and n <= mid_point]
        even_high = [n for n in range(1, self.config.main_pool + 1) if n % 2 == 0 and n > mid_point]
        
        selected = []
        selected.extend(np.random.choice(odd_low, min(target_odd, target_low, len(odd_low)), replace=False))
        selected.extend(np.random.choice(odd_high, min(target_odd - len([s for s in selected if s % 2 == 1]), len(odd_high)), replace=False))
        selected.extend(np.random.choice(even_low, min(target_low - len([s for s in selected if s <= mid_point]), len(even_low)), replace=False))
        
        return list(selected)[:self.config.main_play_count * 2]
    
    def _signal_frequency_cycles(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[int]:
        """Signal 4: Hot numbers that also have good gap timing"""
        
        # Get frequencies
        freq = Counter()
        for i in range(start_idx, end_idx + 1):
            if i >= len(draws):
                break
            for num in draws[i].main_numbers:
                freq[int(num)] += 1
        
        # Get gaps
        last_seen = {}
        for i in range(start_idx, end_idx + 1):
            if i >= len(draws):
                break
            for num in draws[i].main_numbers:
                last_seen[int(num)] = i
        
        # Score = frequency * (1 + gap_normalized)
        scores = {}
        window_size = end_idx - start_idx + 1
        
        for num in range(1, self.config.main_pool + 1):
            frequency = freq.get(num, 0)
            gap = (end_idx - last_seen.get(num, start_idx)) if num in last_seen else window_size
            gap_normalized = gap / window_size
            scores[num] = frequency * (1 + gap_normalized)
        
        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        return [num for num, score in sorted_scores[:self.config.main_play_count * 2]]
    
    def _signal_sum_convergence(self, draws: List[Draw], start_idx: int, end_idx: int) -> List[int]:
        """Signal 5: Select numbers that create sum near historical mean"""
        
        # Calculate historical sum mean
        sums = []
        for i in range(start_idx, end_idx + 1):
            if i >= len(draws):
                break
            sums.append(sum(draws[i].main_numbers))
        
        target_sum = int(np.mean(sums)) if sums else (self.config.main_pool // 2) * self.config.main_count
        
        # Use frequency to guide selection
        freq = Counter()
        for i in range(start_idx, end_idx + 1):
            if i >= len(draws):
                break
            for num in draws[i].main_numbers:
                freq[int(num)] += 1
        
        # Greedy selection to hit target sum
        sorted_freq = sorted(freq.items(), key=lambda x: -x[1])
        selected = []
        current_sum = 0
        
        for num, f in sorted_freq:
            if len(selected) >= self.config.main_play_count:
                break
            
            projected_sum = current_sum + num
            projected_avg = projected_sum / (len(selected) + 1)
            target_avg = target_sum / self.config.main_count
            
            # Add if it keeps us close to target
            if abs(projected_avg - target_avg) < self.config.main_pool / 3:
                selected.append(num)
                current_sum += num
        
        return selected
    
    def _calculate_consensus_confidence(self, avg_votes: float, number_votes: Counter, selected: List[int]) -> float:
        """Calculate confidence based on signal consensus"""
        
        # Base confidence from average votes
        # 5 votes = 100%, 4 votes = 90%, 3 votes = 70%, 2 votes = 50%, 1 vote = 30%
        vote_confidence_map = {5: 1.0, 4: 0.9, 3: 0.7, 2: 0.5, 1: 0.3}
        
        confidences = [vote_confidence_map.get(number_votes[n], 0.3) for n in selected]
        base_confidence = np.mean(confidences)
        
        # Bonus if we have strong consensus numbers (4+ votes)
        strong_consensus = sum(1 for n in selected if number_votes[n] >= 4)
        consensus_bonus = (strong_consensus / len(selected)) * 0.2
        
        total_confidence = min(0.95, base_confidence + consensus_bonus)
        
        return max(0.30, total_confidence)
    
    def calculate_confidence(self, draws: List[Draw], start_idx: int, end_idx: int) -> float:
        return 0.7  # Default high confidence for this strategy