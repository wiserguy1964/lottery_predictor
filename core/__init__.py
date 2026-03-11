"""
Core data fetching and loading functionality

Components:
    - OPAPDataFetcher: Fetches lottery draw data from OPAP API
    - DrawDataLoader: Loads and caches draw data locally

Usage:
    from core import OPAPDataFetcher, DrawDataLoader
    
    fetcher = OPAPDataFetcher(lottery_config)
    loader = DrawDataLoader('OPAP_JOKER')
    draws = loader.get_or_fetch_draws(fetcher)
"""

from .data_fetcher import OPAPDataFetcher, DrawDataLoader
from .unified_loader import get_data_fetcher
from .eurojackpot_fetcher import EurojackpotDataFetcher

__all__ = [
    'OPAPDataFetcher',
    'DrawDataLoader'
]

__version__ = '1.0.0'
