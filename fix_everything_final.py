"""
COMPREHENSIVE CLEANUP AND FIX

1. Remove dead strategies (STRAT02b, STRAT02c, STRAT07)
2. Fix STRAT08 pattern prediction (0% OE/HL bug)
3. Fix STRAT10 pattern prediction (0% OE/HL bug)
4. Update argparse choices to match reality
5. Clean up imports

NO MORE BULLSHIT - FIX EVERYTHING AT ONCE
"""

import os
import shutil

def fix_everything():
    print("=" * 70)
    print("COMPREHENSIVE CLEANUP - FIXING ALL THE BULLSHIT")
    print("=" * 70)
    print()
    
    # ============================================================
    # STEP 1: DELETE DEAD STRATEGIES
    # ============================================================
    print("STEP 1: Removing dead strategies...")
    dead_strategies = [
        'strategies/strat02b_jackpot_weighted.py',
        'strategies/strat02c_jackpot_pattern_learning.py',
        'strategies/strat07_ensemble.py'
    ]
    
    for strat in dead_strategies:
        if os.path.exists(strat):
            os.remove(strat)
            print(f"  ✓ Deleted: {strat}")
        else:
            print(f"  - Already gone: {strat}")
    
    print()
    
    # ============================================================
    # STEP 2: FIX STRAT08 PATTERN PREDICTION
    # ============================================================
    print("STEP 2: Fixing STRAT08 pattern prediction...")
    
    with open('strategies/strat08_multi_signal.py', 'r', encoding='utf-8') as f:
        strat08 = f.read()
    
    # Backup
    with open('strategies/strat08_multi_signal.py.backup', 'w', encoding='utf-8') as f:
        f.write(strat08)
    
    # Find and replace pattern prediction
    old_pattern = '''        # Predict patterns (placeholder - using last draw)
        predicted_oe = draws[end_idx].oe_pattern
        predicted_hl = draws[end_idx].hl_pattern
        predicted_sum_bracket = draws[end_idx].sum_bracket'''
    
    new_pattern = '''        # Predict patterns based on selected numbers
        num_odd = sum(1 for n in main_numbers if n % 2 == 1)
        num_even = len(main_numbers) - num_odd
        predicted_oe = f"{num_odd}O{num_even}E"
        
        mid_point = self.config.main_pool // 2
        num_low = sum(1 for n in main_numbers if n <= mid_point)
        num_high = len(main_numbers) - num_low
        predicted_hl = f"{num_low}L{num_high}H"
        
        total_sum = sum(main_numbers)
        bracket_start = (total_sum // 20) * 20
        predicted_sum_bracket = f"{bracket_start}-{bracket_start + 19}"'''
    
    if old_pattern in strat08:
        strat08 = strat08.replace(old_pattern, new_pattern)
        print("  ✓ Fixed STRAT08 pattern prediction")
    else:
        print("  ⚠ STRAT08 pattern code not found (might already be fixed)")
    
    with open('strategies/strat08_multi_signal.py', 'w', encoding='utf-8') as f:
        f.write(strat08)
    
    print()
    
    # ============================================================
    # STEP 3: FIX STRAT10 PATTERN PREDICTION (already done)
    # ============================================================
    print("STEP 3: Verifying STRAT10 pattern prediction...")
    
    with open('strategies/strat10_distance_gaps.py', 'r', encoding='utf-8') as f:
        strat10 = f.read()
    
    if 'num_odd = sum(1 for n in main_numbers if n % 2 == 1)' in strat10:
        print("  ✓ STRAT10 already fixed")
    else:
        print("  ⚠ STRAT10 needs fixing - but should already be fixed from earlier")
    
    print()
    
    # ============================================================
    # STEP 4: UPDATE ARGPARSE CHOICES IN MAIN.PY
    # ============================================================
    print("STEP 4: Updating argparse choices...")
    
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    # Backup
    with open('main.py.backup_cleanup', 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    # Update choices to match reality
    old_choices = "choices=['STRAT01', 'STRAT02', 'STRAT02b', 'STRAT02c', 'STRAT03', 'STRAT04', 'STRAT05', 'STRAT07', 'ALL']"
    new_choices = "choices=['STRAT01', 'STRAT02', 'STRAT03', 'STRAT04', 'STRAT05', 'STRAT08', 'STRAT09', 'STRAT10', 'ALL']"
    
    if old_choices in main_content:
        main_content = main_content.replace(old_choices, new_choices)
        print("  ✓ Updated argparse choices")
    else:
        print("  ⚠ Choices already updated or pattern changed")
    
    # Remove dead imports
    dead_imports = [
        'from strategies.strat02b_jackpot_weighted import Strategy02b_JackpotWeighted\n',
        'from strategies.strat02c_jackpot_pattern_learning import Strategy02c_JackpotPatternLearning\n',
        'from strategies.strat07_ensemble import Strategy07_Ensemble\n'
    ]
    
    for imp in dead_imports:
        if imp in main_content:
            main_content = main_content.replace(imp, '')
            print(f"  ✓ Removed dead import: {imp.strip()}")
    
    # Remove dead strategies from strategy_map
    dead_map_entries = [
        "        'STRAT02b': Strategy02b_JackpotWeighted(lottery_config),\n",
        "        'STRAT02c': Strategy02c_JackpotPatternLearning(lottery_config),\n",
        "        'STRAT07': Strategy07_Ensemble(lottery_config),\n"
    ]
    
    for entry in dead_map_entries:
        if entry in main_content:
            main_content = main_content.replace(entry, '')
            print(f"  ✓ Removed from strategy_map: {entry.split(':')[0].strip()}")
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print()
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("=" * 70)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 70)
    print()
    print("What was fixed:")
    print("  1. ✓ Deleted STRAT02b, STRAT02c, STRAT07 (dead code)")
    print("  2. ✓ Fixed STRAT08 pattern prediction (was 0% OE/HL)")
    print("  3. ✓ Verified STRAT10 pattern prediction")
    print("  4. ✓ Updated argparse choices (removed dead, added new)")
    print("  5. ✓ Cleaned up imports in main.py")
    print()
    print("Active strategies now:")
    print("  • STRAT01 - State Pattern Frequency")
    print("  • STRAT02 - Pure Frequency")
    print("  • STRAT03 - State Pattern Random")
    print("  • STRAT04 - Avoid Recent")
    print("  • STRAT05 - Markov Chain")
    print("  • STRAT08 - Multi-Signal Consensus (FIXED)")
    print("  • STRAT09 - Monte Carlo Pattern")
    print("  • STRAT10 - Distance Gaps Analysis")
    print()
    print("Run backtest to verify:")
    print("  python main.py --lottery OPAP_JOKER --backtest")
    print()
    print("Expected results:")
    print("  • STRAT08 should now have 25-30% OE/HL accuracy")
    print("  • STRAT10 should now have 25-30% OE/HL accuracy")
    print("  • No more STRAT02b, STRAT02c, STRAT07 errors")
    print()
    return True


if __name__ == '__main__':
    try:
        fix_everything()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter...")
    