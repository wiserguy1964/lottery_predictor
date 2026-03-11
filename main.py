#!/usr/bin/env python3
"""
Lottery Prediction System - Main Application
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

from config import get_lottery_config, get_backtest_config
from core.data_fetcher import DrawDataLoader
from core.unified_loader import get_data_fetcher
from strategies.strat01_state_frequency import Strategy01_StatePatternFreq
from strategies.strat02_pure_frequency import Strategy02_PureFrequency
from strategies.strat03_state_random import Strategy03_StatePatternRandom
from strategies.strat04_avoid_recent import Strategy04_AvoidRecent
from strategies.strat05_markov_chain import Strategy05_MarkovChain
from strategies.strat08_multi_signal import Strategy08_MultiSignalConsensus
from strategies.strat09_monte_carlo import Strategy09_MonteCarloPattern
from strategies.strat07_ensemble import Strategy07_AdaptiveEnsemble
from predictors.joker_predictor import JokerPredictor
from backtesting.rolling_window import RollingWindowBacktester
from visualization.excel_exporter import ExcelExporter
from wheeling.wheel_system import WheelSystem


def main():
    """Main application entry point"""
    
    parser = argparse.ArgumentParser(
        description='Lottery Prediction System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Fetch fresh data
        python main.py --lottery OPAP_JOKER --fetch

        # Run backtest
        python main.py --lottery OPAP_JOKER --backtest

        # Generate predictions
        python main.py --lottery OPAP_JOKER --predict

        # Run full pipeline
        python main.py --lottery OPAP_JOKER --fetch --backtest --predict
                """
    )
    
    parser.add_argument(
        '--lottery',
        default='OPAP_JOKER',
        help='Lottery name (default: OPAP_JOKER)'
    )
    
    parser.add_argument(
        '--fetch',
        action='store_true',
        help='Fetch ALL data from API (full refresh - slow)'
    )
    
    parser.add_argument(
        '--fetch-new',
        action='store_true',
        help='Fetch only NEW draws (incremental - fast!)'
    )

    
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtest on all strategies'
    )
    
    parser.add_argument(
        '--predict',
        action='store_true',
        help='Generate predictions for next draw'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output'),
        help='Output directory for results (default: ./output)'
    )
    
    parser.add_argument(
        '--strategies',
        nargs='+',
        choices=['STRAT01', 'STRAT02', 'STRAT02b', 'STRAT02c', 'STRAT03', 'STRAT04', 'STRAT05', 'STRAT07', 'STRAT08', 'STRAT09', 'ALL'],
        default=['ALL'],
        help='Strategies to test (default: ALL)'
    )
    
    parser.add_argument(
        '--wheel',
        type=int,
        nargs='?',
        const=-1,  # -1 means use config value
        metavar='N',
        help='Generate wheel. Specify N for N numbers, or omit to use main_play_count from config'
    )
    
    parser.add_argument(
        '--wheel-type',
        choices=['auto', 'small', 'medium', 'large', 'full'],
        default='auto',
        help='Wheel type (default: auto)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("LOTTERY PREDICTION SYSTEM")
    print("=" * 70)
    
    # Load configuration
    print(f"\n📊 Loading configuration for {args.lottery}...")
    try:
        lottery_config = get_lottery_config(args.lottery)
        backtest_config = get_backtest_config()
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)
    
    print(f"  ✓ Lottery: {lottery_config.lottery_name}")
    print(f"  ✓ Game ID: {lottery_config.game_id}")
    print(f"  ✓ Main: {lottery_config.main_count}/{lottery_config.main_pool}")
    print(f"  ✓ Bonus: {lottery_config.bonus_count}/{lottery_config.bonus_pool}")
    
    # Initialize components
    fetcher = get_data_fetcher(lottery_config)  # Auto-selects OPAP or EUROJACKPOT fetcher
    loader = DrawDataLoader(args.lottery)
    exporter = ExcelExporter(lottery_config)
    
    # Fetch or load data
    print(f"\n📥 Loading draw data...")
    try:
        # Determine fetch mode
        if args.fetch:
            # Full refresh
            draws = loader.get_or_fetch_draws(fetcher, force_refresh=True, incremental=False)
        elif 'fetch_new' in args and args.fetch_new:
            # Incremental fetch (fast!)
            draws = loader.get_or_fetch_draws(fetcher, force_refresh=False, incremental=True)
        else:
            # Use cache
            draws = loader.get_or_fetch_draws(fetcher, force_refresh=False, incremental=False)
        print(f"  ✓ Loaded {len(draws)} draws")
        if draws:
            print(f"  ✓ Range: {draws[0].draw_id} to {draws[-1].draw_id}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)
    
    if len(draws) < backtest_config.window_size + 10:
        print(f"❌ Not enough draws for backtesting (need at least {backtest_config.window_size + 10})")
        sys.exit(1)
    
    # Initialize strategies
    print(f"\n🎯 Initializing strategies...")
    strategy_map = {
        'STRAT01': Strategy01_StatePatternFreq(lottery_config),
        'STRAT02': Strategy02_PureFrequency(lottery_config),
        'STRAT03': Strategy03_StatePatternRandom(lottery_config),
        'STRAT04': Strategy04_AvoidRecent(lottery_config),
        'STRAT05': Strategy05_MarkovChain(lottery_config),
        'STRAT08': Strategy08_MultiSignalConsensus(lottery_config),
        'STRAT09': Strategy09_MonteCarloPattern(lottery_config),
    }
    
    # Select strategies to use
    if 'ALL' in args.strategies:
        selected_strategies = list(strategy_map.values())
    else:
        selected_strategies = [strategy_map[sid] for sid in args.strategies if sid in strategy_map]
    
    # Add ensemble strategy if using multiple strategies
    # DISABLED: Ensemble causes recursion issues during backtest
    # if len(selected_strategies) > 1:
    #     ensemble = Strategy07_AdaptiveEnsemble(lottery_config, selected_strategies)
    #     selected_strategies.append(ensemble)
    
    for strategy in selected_strategies:
        print(f"  ✓ {strategy.strategy_id}: {strategy.strategy_name}")
    
    # Run backtest
    if args.backtest:
        print(f"\n🔬 Running backtest...")
        print(f"  Window size: {backtest_config.window_size}")
        print(f"  Step size: {backtest_config.step_size}")
        
        backtester = RollingWindowBacktester(lottery_config, backtest_config)
        
        for strategy in selected_strategies:
            backtester.add_strategy(strategy)
        
        try:
            results = backtester.run_backtest(draws, verbose=True)
            summaries = backtester.calculate_summary_metrics(results)
            rankings = backtester.rank_strategies(summaries)
            
            # Display results
            print("\n" + "=" * 70)
            print("BACKTEST RESULTS")
            print("=" * 70)
            
            for rank, (strategy_id, score) in enumerate(rankings, 1):
                if strategy_id not in summaries:
                    continue
                
                metrics = summaries[strategy_id]
                print(f"\n{rank}. {strategy_id} (Score: {score:.1f})")
                print(f"   Main Matches: {metrics['avg_main_matches']:.3f}")
                print(f"   Joker Accuracy: {metrics['joker_accuracy']:.2%}")
                print(f"   OE Accuracy: {metrics['oe_accuracy']:.2%}")
                print(f"   HL Accuracy: {metrics['hl_accuracy']:.2%}")
                print(f"   Tests: {metrics['test_count']}")
            
            # Display Joker method results
            if '_JOKER_METHODS' in summaries:
                print("\n" + "-" * 70)
                print("JOKER METHOD PERFORMANCE")
                print("-" * 70)
                for method, metrics in summaries['_JOKER_METHODS'].items():
                    print(f"  {method}: {metrics['accuracy']:.2%} ({metrics['test_count']} tests)")
            
            # Export to Excel
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backtest_file = args.output_dir / f"backtest_{args.lottery}_{timestamp}.xlsx"
            exporter.export_backtest_results(summaries, rankings, str(backtest_file))
            print(f"\n💾 Results saved to: {backtest_file}")
            
        except Exception as e:
            print(f"❌ Error during backtest: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate predictions
    if args.predict:
        print(f"\n🔮 Generating predictions for next draw...")
        
        # Select BEST strategy for MAIN numbers and BEST method for JOKER
        best_main_strategy = None
        best_joker_method = None
        
        # Only use backtest results if backtest was run
        if args.backtest and 'summaries' in locals():
            # Find best strategy by OVERALL SCORE (same as ranking)
            # Use the #1 ranked strategy for prediction
            if rankings:
                best_strategy_id = rankings[0][0]  # First ranked strategy
                best_overall_score = rankings[0][1]
                best_main_strategy = next(
                    (s for s in selected_strategies if s.strategy_id == best_strategy_id),
                    None
                )
                
                # Get the metrics for display
                best_metrics = summaries.get(best_strategy_id, {})
                best_main_score = best_metrics.get('avg_main_matches', 0)
            else:
                best_main_strategy = None
                best_main_score = 0
                best_overall_score = 0
            
            # Find best method for JOKER (by accuracy)
            if '_JOKER_METHODS' in summaries:
                joker_methods = summaries['_JOKER_METHODS']
                best_joker_acc = 0
                for method, metrics in joker_methods.items():
                    if metrics.get('accuracy', 0) > best_joker_acc:
                        best_joker_acc = metrics['accuracy']
                        best_joker_method = method
            
            if best_main_strategy:
                print(f"  Main numbers: {best_main_strategy.strategy_id} - {best_main_strategy.strategy_name} (rank #1, score: {best_overall_score:.1f}, main matches: {best_main_score:.3f})")
            if best_joker_method:
                print(f"  Joker number: {best_joker_method} method (best accuracy: {best_joker_acc:.2%})")
        
        # Fallback if no backtest
        if best_main_strategy is None:
            best_main_strategy = selected_strategies[0]
            print(f"  Using default strategy: {best_main_strategy.strategy_id} - {best_main_strategy.strategy_name}")
        
        try:
            # Use most recent window for prediction
            window_size = backtest_config.window_size
            start_idx = len(draws) - window_size
            end_idx = len(draws) - 1
            
            # Generate MAIN number prediction
            prediction = best_main_strategy.predict(draws, start_idx, end_idx)
            
            # Generate BONUS numbers
            joker_predictor = JokerPredictor(lottery_config)
            if best_joker_method:
                if best_joker_method == 'FREQUENCY':
                    predicted_bonuses = joker_predictor.predict_frequency(draws, start_idx, end_idx)
                elif best_joker_method == 'AVOID_RECENT':
                    predicted_bonuses = joker_predictor.predict_avoid_recent(draws, start_idx, end_idx)
                elif best_joker_method == 'MARKOV':
                    predicted_bonuses = joker_predictor.predict_markov(draws, start_idx, end_idx)
                elif best_joker_method == 'RANDOM':
                    predicted_bonuses = joker_predictor.predict_random()
                else:
                    predicted_bonuses = joker_predictor.predict_dynamic(draws, start_idx, end_idx)
            else:
                predicted_bonuses = joker_predictor.predict_dynamic(draws, start_idx, end_idx)
            
            # Ensure bonus_numbers is a list with correct count
            import numpy as np
            if isinstance(predicted_bonuses, int):
                bonus_list = [predicted_bonuses]
            elif isinstance(predicted_bonuses, (list, tuple)):
                bonus_list = list(predicted_bonuses)
            else:
                bonus_list = [int(predicted_bonuses)]
            
            # Fill to required count if needed
            while len(bonus_list) < lottery_config.bonus_play_count:
                rand = np.random.randint(1, lottery_config.bonus_pool + 1)
                if rand not in bonus_list:
                    bonus_list.append(rand)
            
            prediction.bonus_numbers = sorted(bonus_list[:lottery_config.bonus_play_count])
            
            # Display prediction
            print("\n" + "=" * 70)
            print("RECOMMENDATION FOR NEXT DRAW")
            print("=" * 70)
            print(f"\nStrategy: {prediction.strategy_name}")
            print(f"Confidence: {prediction.confidence_score:.1%}")
            print(f"\nMain Numbers: {', '.join(map(str, prediction.main_numbers))}")
            print(f"Joker Numbers: {', '.join(map(str, prediction.bonus_numbers))}")
            print(f"\nPredicted Patterns:")
            print(f"  Odd/Even: {prediction.predicted_oe}")
            print(f"  High/Low: {prediction.predicted_hl}")
            print(f"  Sum Bracket: {prediction.predicted_sum_bracket}")
            
            # Play/Skip Recommendation based on confidence
            print("\n" + "=" * 70)
            print("💡 RECOMMENDATION")
            print("=" * 70)
            
            confidence = prediction.confidence_score
            
            if confidence >= 0.70:
                # Very high confidence
                print("\n🟢 STRONG PLAY - High confidence prediction!")
                print(f"   Confidence: {confidence:.1%}")
                print("   The strategy is very confident in these numbers.")
                print("   This is a good opportunity to play.")
            elif confidence >= 0.55:
                # Good confidence
                print("\n🟡 MODERATE PLAY - Reasonable confidence")
                print(f"   Confidence: {confidence:.1%}")
                print("   The strategy has moderate confidence.")
                print("   Consider playing if you feel lucky.")
            elif confidence >= 0.40:
                # Low confidence
                print("\n🟠 WEAK SIGNAL - Low confidence")
                print(f"   Confidence: {confidence:.1%}")
                print("   The strategy struggled to find a strong pattern.")
                print("   Consider skipping unless you're feeling adventurous.")
            else:
                # Very low confidence
                print("\n🔴 SKIP - Very low confidence")
                print(f"   Confidence: {confidence:.1%}")
                print("   The strategy has very little confidence in this prediction.")
                print("   Save your money for a better opportunity.")
            
            print()
            print("Remember: Even high confidence doesn't guarantee a win.")
            print("Lottery odds remain extremely low. Play responsibly!")
            
            # Generate wheel if requested
            wheel_tickets = None
            if args.wheel:
                from wheeling.wheel_system import WheelSystem
                wheel_system = WheelSystem(lottery_config)
                
                # Determine number of numbers to wheel
                if args.wheel == -1:
                    num_for_wheel = len(prediction.main_numbers)
                else:
                    num_for_wheel = args.wheel
                extended_numbers = prediction.main_numbers.copy()
                
                if len(extended_numbers) < num_for_wheel:
                    from analyzers.frequency_analyzer import FrequencyAnalyzer
                    freq_analyzer = FrequencyAnalyzer(lottery_config)
                    all_hot = freq_analyzer.get_hot_numbers(
                        draws, 
                        count=lottery_config.main_pool,
                        start_idx=start_idx,
                        end_idx=end_idx
                    )
                    for num in all_hot:
                        if num not in extended_numbers:
                            extended_numbers.append(num)
                            if len(extended_numbers) >= num_for_wheel:
                                break
                
                wheel_numbers = extended_numbers[:num_for_wheel]
                wheel_type = args.wheel_type if hasattr(args, 'wheel_type') else 'auto'
                wheel_tickets = wheel_system.generate_wheel(
                    wheel_numbers,
                    prediction.bonus_numbers,  # Use ALL bonus numbers
                    wheel_type
                )
                
                print(f"\n{'=' * 70}")
                print(f"WHEEL SYSTEM ({len(wheel_numbers)} numbers → {len(wheel_tickets)} tickets)")
                print(f"{'=' * 70}")
                print(f"\nNumbers in wheel: {', '.join(map(str, wheel_numbers))}")
                print(f"Joker: {', '.join(map(str, prediction.bonus_numbers))}")
                print(f"\nGenerated {len(wheel_tickets)} tickets:")
                for idx, (ticket_main, ticket_bonus) in enumerate(wheel_tickets, 1):
                    print(f"  Ticket {idx:2d}: {', '.join(f'{n:2d}' for n in ticket_main)} + {list(ticket_bonus)}")
                
                cost_per_ticket = lottery_config.ticket_cost
                total_cost = len(wheel_tickets) * cost_per_ticket
                full_coverage_tickets = wheel_system._count_combinations(
                    len(wheel_numbers),
                    lottery_config.main_count
                )
                full_cost = full_coverage_tickets * cost_per_ticket
                savings = ((full_cost - total_cost) / full_cost * 100) if full_cost > 0 else 0
                
                coverage = wheel_system.calculate_coverage(wheel_numbers, wheel_tickets, min_match=3)
                
                print(f"\nCost Analysis:")
                print(f"  Wheel cost: {len(wheel_tickets)} tickets × €{cost_per_ticket:.2f} = €{total_cost:.2f}")
                print(f"  Full coverage: {full_coverage_tickets} tickets × €{cost_per_ticket:.2f} = €{full_cost:.2f}")
                print(f"  Savings: €{full_cost - total_cost:.2f} ({savings:.1f}%)")
                
                print(f"\nCoverage Analysis (Abbreviated Wheel):")
                print(f"  If {len(wheel_numbers)} numbers contain the winning 5:")
                for match_level in sorted(coverage['guaranteed_wins'].keys(), reverse=True):
                    info = coverage['guaranteed_wins'][match_level]
                    if info['percentage'] > 0:
                        guarantee = "✓ GUARANTEED" if info['percentage'] >= 99 else ""
                        print(f"    {match_level} matches: {info['percentage']:5.1f}% ({info['count']:3d}/{coverage['total_combinations']} combos) {guarantee}")
                
                print(f"\n  Note: Abbreviated wheels guarantee good prizes (3-4 matches),")
                print(f"        not jackpots. For guaranteed jackpot, use --wheel-type full.")
            
            # Export to Excel
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pred_file = args.output_dir / f"prediction_{args.lottery}_{timestamp}.xlsx"
            
            if wheel_tickets:
                exporter.export_recommendation_with_wheel(
                    prediction, 
                    draws[-1], 
                    str(pred_file),
                    wheel_tickets,
                    wheel_numbers
                )
            else:
                exporter.export_recommendation(prediction, draws[-1], str(pred_file))
            
            print(f"\n💾 Prediction saved to: {pred_file}")
            
        except Exception as e:
            print(f"❌ Error generating prediction: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()