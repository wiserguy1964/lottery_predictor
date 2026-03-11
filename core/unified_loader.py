"""
Unified Data Loader

Auto-selects the correct fetcher based on lottery type.
"""

from config import LotteryConfig


def get_data_fetcher(lottery_config: LotteryConfig):
    """
    Get appropriate fetcher for the lottery
    
    Returns:
        Fetcher instance (OPAPDataFetcher or EurojackpotDataFetcher)
    """
    lottery_name = lottery_config.lottery_name.upper()
    
    if 'EUROJACKPOT' in lottery_name:
        from core.eurojackpot_fetcher import EurojackpotDataFetcher
        return EurojackpotDataFetcher(lottery_config)
    else:
        from core.data_fetcher import OPAPDataFetcher
        return OPAPDataFetcher(lottery_config)
