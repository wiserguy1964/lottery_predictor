"""
Data fetcher for OPAP lottery API
"""
import requests
import re
import time
from datetime import datetime, timedelta, timedelta, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
from pathlib import Path

from config import LotteryConfig
from models import Draw


class OPAPDataFetcher:
    """Fetches lottery draw data from OPAP API"""
    
    def __init__(self, lottery_config: LotteryConfig):
        """
        Initialize data fetcher
        
        Args:
            lottery_config: Configuration for the specific lottery
        """
        self.config = lottery_config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
    
    def fetch_draws(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_draws: int = 0
    ) -> List[Draw]:
        """
        Fetch draws from OPAP API
        
        Args:
            start_date: Start date (default: lottery's min_date)
            end_date: End date (default: today)
            max_draws: Maximum number of draws to fetch (0 = all)
            
        Returns:
            List of Draw objects
        """
        if start_date is None:
            start_date = self.config.min_date
        
        if end_date is None:
            end_date = datetime.now()
        
        all_draws = []
        current_end = end_date
        chunk_days = 30  # Fetch in 30-day chunks
        
        while current_end >= start_date:
            current_start = current_end - timedelta(days=chunk_days)
            if current_start < start_date:
                current_start = start_date
            
            print(f"Fetching draws from {current_start.date()} to {current_end.date()}...")
            
            chunk_draws = self._fetch_chunk(current_start, current_end)
            all_draws.extend(chunk_draws)
            
            print(f"  Fetched {len(chunk_draws)} draws. Total: {len(all_draws)}")
            
            # Check if we've reached max_draws
            if max_draws > 0 and len(all_draws) >= max_draws:
                all_draws = all_draws[:max_draws]
                break
            
            # Move to next chunk
            current_end = current_start - timedelta(days=1)
            
            # Small delay to be nice to the API
            time.sleep(0.1)
        
        # Sort by draw_id (oldest first)
        all_draws.sort(key=lambda d: int(d.draw_id) if d.draw_id.isdigit() else 0)
        
        return all_draws
    
    def _fetch_chunk(
        self,
        start_date: datetime,
        end_date: datetime,
        retries: int = 3
    ) -> List[Draw]:
        """
        Fetch a single chunk of draws
        
        Args:
            start_date: Start date
            end_date: End date
            retries: Number of retry attempts
            
        Returns:
            List of Draw objects
        """
        url = self.config.api_url_pattern.format(
            game_id=self.config.game_id,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    return self._parse_response(response.text)
                else:
                    print(f"  Warning: HTTP {response.status_code} (attempt {attempt + 1}/{retries})")
            
            except requests.exceptions.RequestException as e:
                print(f"  Error: {e} (attempt {attempt + 1}/{retries})")
            
            if attempt < retries - 1:
                time.sleep(1)  # Wait before retry
        
        print(f"  Failed to fetch chunk after {retries} attempts")
        return []
    
    def _parse_response(self, json_text: str) -> List[Draw]:
        """
        Parse JSON response from OPAP API
        
        Args:
            json_text: Raw JSON response text
            
        Returns:
            List of Draw objects
        """
        draws = []
        
        # Parse using regex (same as VBA code)
        # Pattern: "drawId":12345..."list":[1,2,3,4,5]..."bonus":[10]
        pattern = r'"drawId":(\d+).*?"list":\s*\[([\d,]+)\].*?"bonus":\s*\[(\d+)\]'
        matches = re.finditer(pattern, json_text)
        
        # Also find jackpot wins
        jackpot_pattern = r'"drawId":(\d+).*?"prizeCategories":\s*\[\s*\{[^\}]*"winners":\s*([1-9]\d*)'
        jackpot_matches = re.finditer(jackpot_pattern, json_text)
        jackpot_draws = {m.group(1) for m in jackpot_matches}
        
        for match in matches:
            draw_id = match.group(1)
            main_numbers_str = match.group(2)
            bonus_number_str = match.group(3)
            
            # Parse main numbers
            main_numbers = np.array([int(n) for n in main_numbers_str.split(',')], dtype=int)
            
            # Parse bonus number(s)
            bonus_numbers = np.array([int(bonus_number_str)], dtype=int)
            
            # Create draw object
            draw = Draw(
                draw_id=draw_id,
                date=None,  # API doesn't always provide dates in this format
                main_numbers=main_numbers,
                bonus_numbers=bonus_numbers,
                jackpot_won=(draw_id in jackpot_draws)
            )
            
            draws.append(draw)
        
        return draws


class DrawDataLoader:
    """Loads and saves draw data to/from files"""
    
    def __init__(self, lottery_name: str, data_dir: Optional[Path] = None):
        """
        Initialize data loader
        
        Args:
            lottery_name: Name of lottery (e.g., 'OPAP_JOKER')
            data_dir: Directory for data files (default: ./data)
        """
        self.lottery_name = lottery_name
        
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.data_file = self.data_dir / f"{lottery_name}_history.npz"
    
    def save_draws(self, draws: List[Draw]):
        """
        Save draws to file
        
        Args:
            draws: List of Draw objects
        """
        # Convert to arrays
        draw_ids = [d.draw_id for d in draws]
        main_numbers = np.array([d.main_numbers for d in draws])
        bonus_numbers = np.array([d.bonus_numbers for d in draws])
        jackpot_won = np.array([d.jackpot_won for d in draws])
        
        # Save as compressed numpy file
        np.savez_compressed(
            self.data_file,
            draw_ids=draw_ids,
            main_numbers=main_numbers,
            bonus_numbers=bonus_numbers,
            jackpot_won=jackpot_won
        )
        
        print(f"Saved {len(draws)} draws to {self.data_file}")
    
    def load_draws(self) -> List[Draw]:
        """
        Load draws from file
        
        Returns:
            List of Draw objects
            
        Raises:
            FileNotFoundError: If data file doesn't exist
        """
        if not self.data_file.exists():
            raise FileNotFoundError(
                f"Data file not found: {self.data_file}\n"
                f"Please fetch data first using fetch_draws()"
            )
        
        # Load from file
        data = np.load(self.data_file, allow_pickle=True)
        
        draw_ids = data['draw_ids']
        main_numbers = data['main_numbers']
        bonus_numbers = data['bonus_numbers']
        jackpot_won = data['jackpot_won']
        
        # Convert to Draw objects
        draws = []
        for i in range(len(draw_ids)):
            draw = Draw(
                draw_id=str(draw_ids[i]),
                date=None,
                main_numbers=main_numbers[i],
                bonus_numbers=bonus_numbers[i],
                jackpot_won=bool(jackpot_won[i])
            )
            draws.append(draw)
        
        return draws
    
    def get_or_fetch_draws(
        self,
        fetcher: OPAPDataFetcher,
        force_refresh: bool = False,
        incremental: bool = False
    ) -> List[Draw]:
        """
        Load draws from file, or fetch if not available
        
        Args:
            fetcher: OPAPDataFetcher instance
            force_refresh: If True, always fetch fresh data
            incremental: If True, only fetch new draws since last cached
            
        Returns:
            List of Draw objects
        """
        from datetime import timedelta
        
        if force_refresh:
            print(f"Fetching ALL data for {self.lottery_name}...")
            draws = fetcher.fetch_draws()
            self.save_draws(draws)
            print(f"  ✓ Fetched {len(draws)} draws")
            return draws
        elif incremental:
            # INCREMENTAL FETCH - Only get new draws!
            if self.data_file.exists():
                existing_draws = self.load_draws()
                if existing_draws and len(existing_draws) > 0:
                    latest_draw = existing_draws[-1]
                    latest_id = int(latest_draw.draw_id)
                    
                    print(f"  Latest cached: {latest_draw.draw_id}")
                    print(f"  Checking for new draws...")
                    
                    from datetime import datetime
                    
                    # Fetch backwards in chunks until we find overlap with cached data
                    all_new_draws = []
                    days_back = 30
                    max_days_back = 365  # Don't go back more than 1 year
                    found_overlap = False
                    
                    while days_back <= max_days_back and not found_overlap:
                        start_date = datetime.now() - timedelta(days=days_back)
                        end_date = datetime.now()
                        
                        print(f"  Fetching last {days_back} days...")
                        recent_draws = fetcher.fetch_draws(start_date=start_date, end_date=end_date)
                        
                        # Check which draws are new
                        chunk_new = []
                        has_old_draw = False
                        
                        for draw in recent_draws:
                            try:
                                draw_id = int(draw.draw_id)
                                if draw_id > latest_id:
                                    # This is a new draw
                                    if draw not in all_new_draws:  # Avoid duplicates from overlapping chunks
                                        chunk_new.append(draw)
                                else:
                                    # Found a draw we already have - we've connected!
                                    has_old_draw = True
                            except:
                                pass
                        
                        all_new_draws.extend(chunk_new)
                        
                        if has_old_draw:
                            # We found overlap with cached data - we're done!
                            found_overlap = True
                            print(f"  ✓ Found connection with cached data")
                        elif len(recent_draws) == 0:
                            # No draws in this period - we've gone too far back
                            break
                        else:
                            # No overlap yet, need to fetch further back
                            days_back += 30
                    
                    if all_new_draws:
                        # Remove duplicates and sort by draw_id
                        unique_new = {}
                        for draw in all_new_draws:
                            unique_new[draw.draw_id] = draw
                        
                        new_draws_sorted = sorted(unique_new.values(), key=lambda d: int(d.draw_id))
                        
                        print(f"  ✓ Cached: {len(existing_draws)} | New: {len(new_draws_sorted)}")
                        combined = existing_draws + new_draws_sorted
                        self.save_draws(combined)
                        return combined
                    else:
                        print(f"  ✓ Cached: {len(existing_draws)} | New: 0")
                        print(f"  → Cache is up to date!")
                        return existing_draws
                else:
                    print(f"  Cache is empty, doing full fetch...")
                    draws = fetcher.fetch_draws()
                    self.save_draws(draws)
                    return draws
            else:
                print(f"  No cache file, doing full fetch...")
                draws = fetcher.fetch_draws()
                self.save_draws(draws)
                return draws
        elif not self.data_file.exists():
            print(f"Fetching fresh data for {self.lottery_name}...")
            draws = fetcher.fetch_draws()
            self.save_draws(draws)
            return draws
        else:
            print(f"Loading cached data for {self.lottery_name}...")
            return self.load_draws()

if __name__ == '__main__':
    # Test the data fetcher
    from config import get_lottery_config
    
    config = get_lottery_config('OPAP_JOKER')
    fetcher = OPAPDataFetcher(config)
    loader = DrawDataLoader('OPAP_JOKER')
    
    # Fetch small sample
    draws = fetcher.fetch_draws(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        max_draws=10
    )
    
    print(f"\nFetched {len(draws)} draws")
    if draws:
        print("\nFirst draw:")
        print(draws[0])
        print(f"  OE: {draws[0].get_oe_pattern()}")
        print(f"  HL: {draws[0].get_hl_pattern()}")
        print(f"  Sum: {draws[0].get_sum()}")