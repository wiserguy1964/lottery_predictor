# 🎰 Advanced Lottery Prediction System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A sophisticated lottery prediction system featuring **9 unique strategies**, Monte Carlo simulation, rolling window backtesting, and intelligent wheeling systems. Built for OPAP JOKER and EUROJACKPOT lotteries.

> **⚠️ Educational Project**: This system is for learning about machine learning, statistics, and pattern recognition. **Do not expect consistent profits.** Lottery odds are extremely low, and even the best strategies can barely beat random chance.

---

## 🌟 Key Features

### 🧠 **9 Advanced Prediction Strategies**
- **STRAT01**: State Pattern Frequency Analysis
- **STRAT02**: Pure Frequency-Based Prediction
- **STRAT03**: State Patterns + Random (🏆 Best performer: 79.9 score)
- **STRAT04**: Avoid Recently Drawn Numbers
- **STRAT05**: Markov Chain Transition Probabilities
- **STRAT08**: Multi-Signal Consensus (5 independent signals)
- **STRAT09**: Monte Carlo Pattern Matching (5,000 simulations)

### 📊 **Sophisticated Backtesting**
- Rolling window backtesting with 500+ test windows
- Configurable window size (40-120 draws)
- Multiple performance metrics (matches, OE/HL accuracy, confidence)
- Automatic strategy ranking and comparison
- Beautiful Excel reports with detailed breakdowns

### ⚡ **Smart Data Management**
- **Incremental Fetch**: Only downloads new draws (5 seconds vs 5 minutes!)
- Automatic caching system
- Handles multi-month gaps automatically
- Duplicate detection and prevention
- Resilient error handling with auto-retry

### 🎡 **Intelligent Wheeling System**
- Abbreviated wheels (6-20 numbers → 8-25 tickets)
- Full coverage wheels for guaranteed prizes
- Automatic cost/coverage analysis
- Smart wheel type selection
- Prize probability calculations

### 📈 **Confidence-Based Recommendations**
- 🟢 **Strong Play** (≥70%): Clear patterns detected
- 🟡 **Moderate Play** (55-70%): Reasonable confidence
- 🟠 **Weak Signal** (40-55%): Unclear patterns
- 🔴 **Skip** (<40%): Very low confidence - save your money

---

## 📸 Sample Output

```
BACKTEST RESULTS
======================================================================
1. STRAT03 (Score: 79.9)
   Main Matches: 1.031
   Joker Accuracy: 5.44%
   OE Accuracy: 29.40%
   HL Accuracy: 30.67%
   Tests: 551

RECOMMENDATION FOR NEXT DRAW
======================================================================
Strategy: State Patterns + Random
Confidence: 50.0%

Main Numbers: 13, 15, 26, 28, 30, 32, 34, 38, 40
Joker Numbers: 14

💡 RECOMMENDATION
🟠 WEAK SIGNAL - Low confidence
   Consider skipping unless you're feeling adventurous.

WHEEL SYSTEM (9 numbers → 8 tickets)
======================================================================
  Ticket 1: 13, 15, 26, 28, 30 + [14]
  Ticket 2: 13, 15, 32, 34, 38 + [14]
  ...
Cost: €4.00 (8 tickets × €0.50)
Full coverage: €63.00 (252 tickets)
Savings: €59.00 (93.7%)
```

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip (Python package manager)
```

### Installation

```bash
# Clone the repository
git clone https://github.com/wiserguy1964/lottery_predictor.git
cd lottery_predictor

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# 1. Fetch latest draw data (first time - slow)
python main.py --lottery OPAP_JOKER --fetch

# 2. Run backtest to find best strategy
python main.py --lottery OPAP_JOKER --backtest

# 3. Generate prediction with wheeling
python main.py --lottery OPAP_JOKER --predict --wheel

# 4. Daily workflow (incremental fetch + prediction)
python main.py --lottery OPAP_JOKER --fetch-new --predict --wheel
```

---

## 📖 Advanced Usage

### Incremental Data Fetching (⚡ Fast!)

```bash
# Only fetch new draws since last update (5 seconds instead of 5 minutes!)
python main.py --lottery OPAP_JOKER --fetch-new

# First time or monthly refresh (fetches all historical data)
python main.py --lottery OPAP_JOKER --fetch
```

**How it works:**
1. Checks latest cached draw ID (e.g., 3029)
2. Fetches only recent draws from API
3. Filters for draws > 3029
4. Appends new draws to cache (no duplicates!)

### Testing Specific Strategies

```bash
# Test your top 3 strategies
python main.py --lottery OPAP_JOKER --backtest --strategies STRAT03 STRAT09 STRAT02

# Compare all strategies
python main.py --lottery OPAP_JOKER --backtest --strategies ALL
```

### Custom Wheel Generation

```bash
# Generate wheel with 12 numbers
python main.py --lottery OPAP_JOKER --predict --wheel 12

# Use main_play_count from config (default: 9)
python main.py --lottery OPAP_JOKER --predict --wheel

# Specify wheel type
python main.py --lottery OPAP_JOKER --predict --wheel 15 --wheel-type full
```

### EUROJACKPOT Support

```bash
# Same commands work for EUROJACKPOT
python main.py --lottery EUROJACKPOT --fetch-new --predict --wheel
```

---

## ⚙️ Configuration

Edit `lottery_config.xlsx` to customize:

### Lottery Parameters (Sheet: LOTTERY_CONFIGS)
- `lottery_name`: OPAP_JOKER, EUROJACKPOT
- `main_count`: Numbers drawn (5 for JOKER)
- `main_pool`: Number pool size (45 for JOKER)
- `main_play_count`: Numbers to recommend (6-12 for wheeling)
- `bonus_count`: Bonus numbers drawn (1 for JOKER, 2 for EUROJACKPOT)

### Backtest Parameters (Sheet: BACKTEST_PARAMS)
- `window_size`: **60** (recommended) - Rolling window size
- `step_size`: **5** (recommended) - Window step size
- `fetch_chunk_days`: **30** - API fetch chunk size

**Window Size Impact:**
| Size | Use Case | Performance |
|------|----------|-------------|
| 40 | Fast, recent patterns | Good for STRAT03 |
| 60 | **Balanced (recommended)** | Good for most strategies |
| 80-100 | Stable patterns | Better for STRAT09 |
| 120+ | Very stable, slow to adapt | Research/experimentation |

---

## 📁 Project Structure

```
lottery_predictor/
├── main.py                          # Main application entry point
├── config.py                        # Configuration loader and manager
├── lottery_config.xlsx              # Lottery and backtest configuration
│
├── strategies/                      # Prediction strategies (the brain)
│   ├── base_strategy.py            # Base class for all strategies
│   ├── strat01_state_frequency.py  # State-based frequency analysis
│   ├── strat02_pure_frequency.py   # Simple frequency counting
│   ├── strat03_state_random.py     # State patterns + randomization
│   ├── strat04_avoid_recent.py     # Avoid recently drawn numbers
│   ├── strat05_markov_chain.py     # Markov transition probabilities
│   ├── strat08_multi_signal.py     # 5-signal consensus
│   └── strat09_monte_carlo.py      # Monte Carlo pattern matching
│
├── core/                           # Core functionality
│   ├── data_fetcher.py            # OPAP/EUROJACKPOT API integration
│   ├── unified_loader.py          # Smart data loader with caching
│   └── eurojackpot_fetcher.py     # EUROJACKPOT web scraper
│
├── predictors/                     # Bonus number prediction
│   └── joker_predictor.py         # 4 methods: Frequency, Avoid Recent, Markov, Dynamic
│
├── analyzers/                      # Pattern analysis
│   ├── frequency_analyzer.py      # Hot/cold number detection
│   ├── pattern_analyzer.py        # OE/HL/Sum pattern analysis
│   └── markov_analyzer.py         # Transition probability calculator
│
├── backtesting/                    # Backtesting engine
│   └── rolling_window.py          # Rolling window backtest framework
│
├── wheeling/                       # Wheel generation
│   └── wheel_system.py            # Abbreviated/full wheel generator
│
├── visualization/                  # Output and reporting
│   └── excel_exporter.py          # Beautiful Excel report generation
│
├── models/                         # Data models
│   └── __init__.py                # Draw, Prediction, LotteryConfig classes
│
└── data/                          # Cached draw data (gitignored)
    └── OPAP_JOKER_history.npz     # Compressed draw cache
```

---

## 🎯 Strategy Comparison

**Performance with window_size=60 (551 test windows):**

| Rank | Strategy | Score | Main Matches | Joker | OE Acc | HL Acc | Notes |
|------|----------|-------|--------------|-------|--------|--------|-------|
| 🥇 1 | **STRAT03** | **79.9** | **1.031** | 5.44% | 29.40% | 30.67% | Best overall |
| 🥈 2 | STRAT02 | 77.1 | 0.995 | 5.08% | 25.77% | 22.50% | Reliable baseline |
| 🥉 3 | STRAT05 | 77.0 | 1.020 | 4.90% | 25.77% | 22.50% | Good transitions |
| 4 | STRAT04 | 75.7 | 0.947 | 5.26% | 25.77% | 22.50% | Cold number expert |
| 5 | STRAT01 | 72.2 | 0.995 | 4.17% | 29.40% | 30.67% | Good patterns |
| 6 | STRAT09 | 72.1 | 1.002 | 4.17% | 28.86% | 28.86% | Better with larger windows |
| 7 | STRAT08 | 58.5 | 0.933 | 3.81% | 0.00% | 0.00% | Needs fixing |

**Joker Method Performance:**
- 🥇 **AVOID_RECENT**: 5.81% (Best joker predictor)
- 🥈 RANDOM: 5.26%
- 🥉 FREQUENCY: 4.36%
- MARKOV: 4.17%

**Key Insights:**
- Main matches >1.0 = Better than random
- STRAT03 averages **1.031 matches** (3.1% better than expected 1.0)
- Pattern accuracy (OE/HL) varies 22-31% (random = ~20%)
- Confidence varies 30-70% based on current data patterns

---

## 🧮 Understanding the Metrics

### Main Matches
**Average number of correct predictions per draw**

Example: Predict [2, 8, 13, 24, 29, 31, 36, 38, 41] (9 numbers)
- Actual draw: [8, 13, 17, 22, 35]
- **Matches: 2** (numbers 8 and 13)

**Interpretation:**
- 1.0 matches = Random chance (expected with 9 numbers)
- 1.1 matches = 10% better than random (good!)
- 1.5 matches = Exceptional (very rare)
- 2.0 matches = Would make you rich (impossible long-term)

### Confidence Score
**How certain the strategy is about THIS prediction**

**NOT the same as backtest score!**
- Backtest score = Historical performance
- Confidence = Current prediction certainty

**What affects confidence:**
- Pattern strength in recent draws
- Signal agreement across methods
- Constraint satisfaction difficulty

### OE/HL Accuracy
**Pattern prediction accuracy**

Predicts odd/even and high/low distributions:
- OE: "3O2E" = 3 odd, 2 even numbers
- HL: "2L3H" = 2 low (1-22), 3 high (23-45)

**Random baseline:** ~20%  
**Good performance:** 25-35%  
**Exceptional:** >40%

---

## ⚠️ Reality Check

### What This System CAN Do:
✅ Analyze historical patterns in lottery data  
✅ Identify numbers slightly more likely than random  
✅ Generate intelligent wheel combinations  
✅ Provide honest confidence assessments  
✅ Save time with incremental data fetching  
✅ Compare multiple prediction strategies  

### What This System CANNOT Do:
❌ Predict lottery numbers with certainty  
❌ Beat the house edge consistently  
❌ Make you rich  
❌ Overcome fundamental randomness  
❌ Guarantee any level of success  

### The Math Reality:
```
OPAP JOKER Jackpot Odds: 1 in 24,435,180

Even with 1.031 average matches (3% better than random):
- Your odds improve to: ~1 in 23,000,000
- Still essentially impossible
- Expected long-term result: Loss

This is an EDUCATIONAL project about:
✓ Machine learning and pattern recognition
✓ Statistical analysis and probability
✓ Software engineering and architecture
✓ Data processing and optimization

NOT a get-rich-quick scheme!
```

---

## 🛠️ Development

### Adding New Strategies

1. Create new file: `strategies/strat10_your_strategy.py`

```python
from models import Draw, Prediction
from strategies.base_strategy import BaseStrategy
from config import LotteryConfig

class Strategy10_YourStrategy(BaseStrategy):
    def __init__(self, lottery_config: LotteryConfig):
        super().__init__(
            lottery_config,
            "STRAT10",
            "Your Strategy Name"
        )
    
    def predict(self, draws, start_idx, end_idx):
        # Your prediction logic here
        
        # Example: Select random numbers
        import numpy as np
        main_numbers = sorted(np.random.choice(
            range(1, self.config.main_pool + 1),
            size=self.config.main_play_count,
            replace=False
        ))
        
        bonus_numbers = [self.config.bonus_pool // 2]
        
        return Prediction(
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            main_numbers=main_numbers,
            bonus_numbers=bonus_numbers,
            predicted_oe="3O2E",
            predicted_hl="2L3H",
            predicted_sum_bracket="100-119",
            confidence_score=0.5
        )
    
    def calculate_confidence(self, draws, start_idx, end_idx):
        return 0.5
```

2. Add to `main.py`:

```python
from strategies.strat10_your_strategy import Strategy10_YourStrategy

strategy_map = {
    # ... existing strategies ...
    'STRAT10': Strategy10_YourStrategy(lottery_config),
}
```

3. Test it:

```bash
python main.py --lottery OPAP_JOKER --backtest --strategies STRAT10
```

### Running Custom Tests

```bash
# Test with different window sizes
# Edit lottery_config.xlsx: window_size = 80
python main.py --lottery OPAP_JOKER --backtest

# Test incremental fetch
python main.py --lottery OPAP_JOKER --fetch-new

# Test wheel generation
python main.py --lottery OPAP_JOKER --predict --wheel 15 --wheel-type full
```

---

## 🐛 Troubleshooting

### "ImportError: No module named 'X'"
```bash
pip install -r requirements.txt
```

### "Error loading data: File not found"
```bash
# Fetch data for the first time
python main.py --lottery OPAP_JOKER --fetch
```

### "Invalid choice: STRATXX"
```bash
# Make sure strategy is added to:
# 1. main.py imports
# 2. strategy_map dictionary
# 3. argparse choices list
```

### Slow backtest
```bash
# Reduce window_size in lottery_config.xlsx: 60 → 40
# Or reduce strategies tested
python main.py --backtest --strategies STRAT03 STRAT09
```

### Low confidence predictions
This is normal! It means:
- Current data has weak patterns
- System is being honest
- Consider waiting for better conditions

---

## 📊 Excel Reports

The system generates beautiful Excel reports with:

**Backtest Sheet:**
- Strategy rankings and scores
- Detailed performance metrics
- Joker method comparison
- Test statistics

**Prediction Sheet:**
- Recommended numbers
- Confidence assessment
- Pattern predictions
- Last draw information

**Wheel Sheet** (when using --wheel):
- All generated tickets
- Cost analysis
- Coverage statistics
- Prize probabilities

Files saved to: `output/backtest_OPAP_JOKER_YYYYMMDD_HHMMSS.xlsx`

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- 🧠 **New Strategies**: Neural networks, genetic algorithms, ensemble methods
- 📊 **Better Analysis**: Advanced pattern recognition, temporal analysis
- 🎡 **Wheel Optimization**: More efficient wheel designs, cost optimization
- 🌍 **More Lotteries**: Support for additional lottery games
- ⚡ **Performance**: Cython optimization, parallel processing
- 📱 **UI**: Web interface, mobile app

---

## 📄 License

MIT License - See LICENSE file for details

**Use freely, modify as needed, but:**
- No warranty provided
- Use at your own risk
- Gambling is risky - play responsibly
- Expected long-term result: Loss

---

## 🙏 Acknowledgments

**Built with:**
- **Python 3.8+**: Core language
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation
- **scikit-learn**: Machine learning utilities
- **OpenPyXL**: Excel file generation
- **Requests**: API communication
- **BeautifulSoup4**: Web scraping

**Inspired by:**
- Statistical lottery analysis research
- Machine learning pattern recognition
- Monte Carlo simulation techniques
- Professional software engineering practices

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/wiserguy1964/lottery_predictor/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/wiserguy1964/lottery_predictor/discussions)
- 📧 **Contact**: Open an issue for questions

---

## ⭐ Star This Project

If you find this project useful, interesting, or educational, please give it a star! ⭐

It helps others discover the project and motivates continued development.

---

<div align="center">

**Remember: This is for educational purposes.**  
**Lottery is gambling. The house always wins.**  
**Play responsibly! 🎲**

---

Made with ❤️ and a healthy dose of statistical skepticism

</div>