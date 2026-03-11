# Wheeling System Explanation

## Types of Wheels

### **Abbreviated Wheels** (Default)

**What they do:**
- **Guarantee 3 matches**: 100% of the time
- **Guarantee 4 matches**: 85-95% of the time  
- **Hit 5 matches (jackpot)**: 5-10% of the time

**Example: 9 numbers**
- Abbreviated: 8 tickets = €8
- Coverage: 4+ matches in 86.5% of cases
- If winning 5 are in your 9: You win 4 matches 87% of the time

**Why use them:**
- ✅ 93% cost savings (€8 vs €126)
- ✅ Guaranteed good prizes (3-4 matches)
- ✅ Still have a chance at jackpot (6-7%)
- ✅ Best value for money

**Best for:**
- Regular players who want consistent smaller wins
- Budget-conscious players
- Playing multiple draws

---

### **Full Wheels**

**What they do:**
- **Guarantee 5 matches**: 100% (jackpot guaranteed!)
- **Guarantee 4 matches**: 100%
- **Guarantee 3 matches**: 100%

**Example: 9 numbers**
- Full wheel: 126 tickets = €126
- Coverage: 100% of all combinations
- If winning 5 are in your 9: You WILL win the jackpot

**Why use them:**
- ✅ Absolute guarantee of jackpot if numbers are right
- ✅ Maximum possible coverage

**Drawbacks:**
- ❌ Extremely expensive (€126 for just 9 numbers!)
- ❌ Only practical for small pools (6-8 numbers)

**Best for:**
- High-confidence situations
- Syndicates splitting costs
- Special draws (when jackpot is huge)

---

## Coverage Comparison

| Numbers | Abbreviated | Full | Savings |
|---------|-------------|------|---------|
| 6 | 6 tickets (€6) | 6 tickets (€6) | €0 (0%) |
| 7 | 7 tickets (€7) | 21 tickets (€21) | €14 (67%) |
| 8 | 8 tickets (€8) | 56 tickets (€56) | €48 (86%) |
| 9 | 8 tickets (€8) | 126 tickets (€126) | €118 (94%) |
| 10 | 12 tickets (€12) | 252 tickets (€252) | €240 (95%) |
| 12 | 15 tickets (€15) | 792 tickets (€792) | €777 (98%) |

**As you add more numbers, abbreviated wheels become increasingly valuable!**

---

## Which Should You Use?

### **Use Abbreviated (Default)** when:
- Playing regularly (most cost-effective)
- Want consistent 3-4 match prizes
- Budget is limited
- Playing 9+ numbers

### **Use Full** when:
- Extremely confident in your number selection
- Can afford the cost
- Playing only 6-8 numbers (still affordable)
- Special occasion / huge jackpot

---

## Understanding the Math

**Abbreviated Wheel for 9 numbers:**
```
126 possible 5-number combinations
8 tickets cover:
- 8 combinations exactly (6.3%)
- 109 combinations with 4 matches (86.5%)
- 9 combinations with 3 matches (7.1%)
```

**What this means:**
- If the winning 5 are in your 9 numbers:
  - 6.3% chance: You win jackpot (5/5)
  - 86.5% chance: You win 4/5 (still good prize!)
  - 7.1% chance: You win 3/5 (smaller prize)
  - 0% chance: You get less than 3 matches

**Expected value is excellent** - you're almost certain to win SOMETHING if your numbers are good!

---

## Command Reference

```bash
# Abbreviated wheel (default) - best value
python main.py --predict --wheel 9

# Full wheel - 100% guarantee (expensive)
python main.py --predict --wheel 9 --wheel-type full

# Cost estimate only
python main.py --predict --wheel 12  # Shows cost comparison
```

---

## Recommendation

**For most players: Use abbreviated wheels (default)**

They provide the best balance of:
- Cost savings (90-95% cheaper)
- Prize guarantee (100% for 3+, 85-95% for 4+)
- Still have jackpot chances (5-10%)

The strategy's job is to pick the right numbers. The abbreviated wheel ensures you don't leave empty-handed if you picked well!
