"""
Manual EUROJACKPOT Data Import

If OPAP API doesn't have EUROJACKPOT, use this script to import
data from a CSV file.

CSV Format Expected:
draw_id,date,n1,n2,n3,n4,n5,b1,b2
12345,2024-01-05,3,12,23,34,41,2,7
12346,2024-01-12,5,15,25,35,45,4,9
...

Usage:
1. Save your EUROJACKPOT data as eurojackpot_data.csv
2. Run: python import_eurojackpot_data.py
"""

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from config import get_lottery_config
from models import Draw


def import_from_csv(csv_file: str, lottery_name: str = 'EUROJACKPOT'):
    """
    Import EUROJACKPOT data from CSV
    
    Args:
        csv_file: Path to CSV file
        lottery_name: Lottery name (default: EUROJACKPOT)
    """
    
    print(f"Importing {lottery_name} data from {csv_file}...")
    
    # Load config
    config = get_lottery_config(lottery_name)
    
    # Read CSV
    df = pd.read_csv(csv_file)
    
    print(f"Found {len(df)} draws in CSV")
    
    # Convert to Draw objects
    draws = []
    
    for _, row in df.iterrows():
        # Parse date
        date = pd.to_datetime(row['date'])
        
        # Get main numbers (first 5 columns: n1-n5)
        main_numbers = np.array([
            row['n1'], row['n2'], row['n3'], row['n4'], row['n5']
        ], dtype=int)
        
        # Get bonus numbers (next 2 columns: b1-b2)
        bonus_numbers = np.array([
            row['b1'], row['b2']
        ], dtype=int)
        
        draw = Draw(
            draw_id=str(row['draw_id']),
            date=date,
            main_numbers=main_numbers,
            bonus_numbers=bonus_numbers
        )
        
        draws.append(draw)
    
    # Sort by date (oldest first)
    draws.sort(key=lambda d: d.date if d.date else datetime.min)
    
    print(f"Converted {len(draws)} draws")
    
    # Save to NPZ format
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    output_file = data_dir / f'{lottery_name}_history.npz'
    
    # Prepare data for NPZ
    draw_ids = np.array([d.draw_id for d in draws])
    dates = np.array([d.date.isoformat() if d.date else '' for d in draws])
    main_numbers = np.array([d.main_numbers for d in draws])
    bonus_numbers = np.array([d.bonus_numbers for d in draws])
    
    np.savez_compressed(
        output_file,
        draw_ids=draw_ids,
        dates=dates,
        main_numbers=main_numbers,
        bonus_numbers=bonus_numbers
    )
    
    print(f"✓ Saved to {output_file}")
    print(f"✓ Ready to use with --lottery {lottery_name}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python import_eurojackpot_data.py <csv_file>")
        print()
        print("CSV format:")
        print("  draw_id,date,n1,n2,n3,n4,n5,b1,b2")
        print("  12345,2024-01-05,3,12,23,34,41,2,7")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    import_from_csv(csv_file)
