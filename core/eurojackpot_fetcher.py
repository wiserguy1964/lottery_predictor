"""
EUROJACKPOT Data Fetcher - Web Scraping

Scrapes euro-jackpot.net for historical data.
Credit: Based on working scraper from user's friend.
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from typing import List, Optional
import numpy as np

from config import LotteryConfig
from models import Draw


class EurojackpotDataFetcher:
    """Fetches EUROJACKPOT by scraping euro-jackpot.net"""
    
    BASE_URL = "https://www.euro-jackpot.net/en/results-archive-{year}"
    
    def __init__(self, lottery_config: LotteryConfig):
        self.config = lottery_config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        })
    
    def fetch_draws(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_draws: int = 0
    ) -> List[Draw]:
        """Fetch draws by scraping historical archives"""
        
        if start_date is None:
            start_date = self.config.min_date
        if end_date is None:
            end_date = datetime.now()
        
        print(f"Fetching EUROJACKPOT from euro-jackpot.net...")
        print(f"Range: {start_date.date()} to {end_date.date()}")
        print()
        
        start_year = start_date.year
        end_year = end_date.year
        
        all_draws = []
        
        for year in range(start_year, end_year + 1):
            year_draws = self._fetch_year(year)
            
            for draw in year_draws:
                if draw.date and start_date <= draw.date <= end_date:
                    all_draws.append(draw)
                    if max_draws > 0 and len(all_draws) >= max_draws:
                        break
            
            if max_draws > 0 and len(all_draws) >= max_draws:
                break
            
            time.sleep(0.5)
        
        all_draws.sort(key=lambda d: d.date if d.date else datetime.min)
        
        print(f"\nTotal: {len(all_draws)} draws")
        if all_draws:
            print(f"Range: {all_draws[0].date.date()} to {all_draws[-1].date.date()}")
        
        return all_draws
    
    def _fetch_year(self, year: int) -> List[Draw]:
        """Fetch all draws for a year"""
        
        url = self.BASE_URL.format(year=year)
        print(f"Year {year}...", end=' ')
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"✗ {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("⚠ No table")
            return []
        
        draws = []
        for row in table.find_all('tr')[1:]:
            draw = self._parse_row(row)
            if draw:
                draws.append(draw)
        
        print(f"✓ {len(draws)} draws")
        return draws
    
    def _parse_row(self, row) -> Optional[Draw]:
        """Parse table row"""
        
        cells = row.find_all('td')
        if len(cells) < 2:
            return None
        
        # Date
        date_link = cells[0].find('a')
        if not date_link or not date_link.get('href'):
            return None
        
        date_part = date_link['href'].split('/')[-1]
        try:
            draw_date = datetime.strptime(date_part, "%d-%m-%Y")
        except ValueError:
            return None
        
        # Numbers - primary: <li> elements
        ball_lis = cells[1].find_all('li')
        
        if len(ball_lis) == 7:
            try:
                numbers = [int(li.get_text(strip=True)) for li in ball_lis]
            except ValueError:
                return None
        else:
            # Fallback: space-separated
            text = cells[1].get_text(strip=True, separator=' ')
            numbers = [int(p) for p in text.split() if p.isdigit()]
        
        if len(numbers) != 7:
            return None
        
        return Draw(
            draw_id=draw_date.strftime("%Y%m%d"),
            date=draw_date,
            main_numbers=np.array(numbers[:5], dtype=int),
            bonus_numbers=np.array(numbers[5:7], dtype=int)
        )
