---
doc_type: methodology_docs
linkage_level: global
variant_id: monte_carlo_simulation_guide
word_count_target: 1500
placeholders:
  required: []
---

# Monte Carlo Simulation: Understanding Our Projection Methodology

**Document Type**: Quantitative Methodology  
**Topic**: Monte Carlo Simulation for Portfolio Projections  
**Effective Date**: March 2026  
**Classification**: Internal - Investment Education

---

## Introduction

When planning for long-term financial goals, one of the most important questions is: "What might my portfolio be worth in 10, 20, or 30 years?" The honest answer is that no one can predict the future with certainty. However, we can do something better than making a single guess—we can explore thousands of possible futures based on how markets have actually behaved.

This is what Monte Carlo simulation does. Named after the famous casino in Monaco (because it involves random numbers, like rolling dice), Monte Carlo simulation is a technique that runs thousands of possible scenarios to help us understand the range of outcomes we might experience.

---

## The Concept: Planning for Uncertainty

### A Simple Analogy

Imagine you're planning a road trip from London to Edinburgh. You could estimate it takes 7 hours based on the distance and speed limit. But in reality, your journey time depends on many unpredictable factors: traffic, weather, road works, how many stops you take.

Instead of assuming exactly 7 hours, imagine you could simulate 10,000 versions of that trip, each with different combinations of traffic, weather, and stops—all based on actual historical data about UK road conditions. You might find:

- Best case: 6 hours (light traffic, no stops)
- Typical case: 7.5 hours (normal conditions)
- Worst case: 10 hours (heavy traffic, weather delays)
- There's a 90% chance you'll arrive within 8.5 hours

This gives you much more useful information for planning than a single estimate.

Monte Carlo simulation does exactly this for investment portfolios—it explores thousands of possible market scenarios to help you understand not just what might happen, but what could happen across a wide range of circumstances.

---

## How Our Implementation Works

Our Monte Carlo simulation follows four key steps to generate realistic future scenarios.

### Step 1: Learning from History

We start by analysing how your portfolio's assets have actually performed historically. For each asset, we calculate:

- **The general trend**: On average, do returns tend to be positive or negative? By how much? This is called the "drift."
- **The random variations**: How much do daily returns bounce around that average trend? These are the "residuals"—the part of returns that can't be predicted.

Think of it like analysing your commute to work. If you typically arrive within 5 minutes of 8:30am, but some days you're 15 minutes early and other days 20 minutes late, we want to capture both the typical pattern and the range of variations.

### Step 2: Block Bootstrapping (Preserving Market Behaviour)

Here's where our approach gets sophisticated. Instead of treating each day's market movement as completely independent, we recognise that markets have "memory." Bad days often cluster together (think of a market correction), and good days can form winning streaks.

**What is block bootstrapping?**

Rather than picking individual random days from history, we pick random *blocks* of consecutive days. Our blocks are 21 trading days long—roughly one month.

**Why does this matter?**

If you've ever noticed that market volatility seems to come in waves—calm periods followed by turbulent periods—that's exactly what we're preserving. By keeping days in their original sequences, we maintain realistic patterns:

- The tendency for volatility to cluster
- How returns can trend for short periods
- The natural rhythm of market movements

This makes our simulations more realistic than simpler approaches that assume each day is independent.

### Step 3: Running 10,000 Simulated Futures

With our building blocks in place, we generate 10,000 complete simulations of your portfolio's future. Each simulation:

1. Starts with your current portfolio value
2. Applies the general market trend (drift)
3. Adds random variations by selecting blocks of historical residuals
4. Tracks the portfolio value day by day
5. Optionally adds regular contributions (if you're investing monthly)

Each simulation produces a different possible future—some optimistic, some pessimistic, most somewhere in the middle.

**Dollar-Cost Averaging Support**

If you're making regular investments over time, our simulation handles this properly. For each monthly contribution, we:

- Add the specified amount to your portfolio
- Account for growth in your contribution amount (if specified)
- Continue the simulation with the new total

This helps answer questions like: "If I invest £1,000 per month for the next 20 years, what range of outcomes might I expect?"

### Step 4: Analysing the Distribution of Outcomes

After running all 10,000 simulations, we analyse the full range of results. This gives us:

**Percentile Values**
- 5th percentile: Only 5% of simulations ended below this value (near worst case)
- 25th percentile: The lower quarter boundary
- 50th percentile: The median—half of simulations above, half below
- 75th percentile: The upper quarter boundary
- 95th percentile: Only 5% of simulations exceeded this value (near best case)

**Probability Metrics**
- Probability of reaching your goal
- Probability of maintaining your principal
- Probability of achieving various return thresholds

---

## Key Parameters

| Parameter | Our Setting | Why This Matters |
|-----------|-------------|------------------|
| Number of simulations | 10,000 | Provides statistically robust results |
| Block size | 21 days | Preserves monthly market patterns |
| Trading days per year | 252 | Standard market convention |
| Contribution frequency | Monthly | Aligned with typical investment patterns |

---

## Interpreting Your Results

When reviewing Monte Carlo results, focus on these key insights:

### The Distribution Range

Look at the spread between the 5th and 95th percentiles. A wide range indicates high uncertainty—which might suggest a more volatile portfolio. A narrower range suggests more predictable outcomes.

### The Median vs. Average

The median (50th percentile) is often more useful than the average because extreme outliers don't skew it. If the average is much higher than the median, it means a small number of very positive scenarios are pulling the average up.

### Goal Achievement Probability

If you have a specific target (e.g., £1 million for retirement), the probability of reaching it provides a straightforward answer to "Am I on track?"

### Worst-Case Scenarios

The 5th or 10th percentile shows what might happen in adverse conditions. This helps with questions like "Can I afford to retire even if markets perform poorly?"

---

## Why This Matters for Financial Planning

Traditional projections often assume a single growth rate: "If your portfolio grows at 7% annually..." But this oversimplifies reality. Markets don't grow steadily—they fluctuate, sometimes dramatically.

Monte Carlo simulation addresses this by:

1. **Acknowledging uncertainty**: No one knows exactly what will happen
2. **Quantifying risk**: Understanding the range of possible outcomes
3. **Enabling better decisions**: Plan for realistic scenarios, not just averages
4. **Stress testing**: See how plans hold up in difficult market conditions

By understanding the full range of possibilities, you can make more informed decisions about savings rates, retirement timing, risk tolerance, and goal setting.

---

## Technical Foundation

Our Monte Carlo engine runs entirely within Snowflake, processing all 10,000 simulations in parallel for fast results. The implementation uses advanced SQL and user-defined functions to perform complex statistical calculations efficiently, ensuring you receive projections quickly even for multi-decade time horizons.

---

**Document Version**: 1.0  
**Last Updated**: March 2026
