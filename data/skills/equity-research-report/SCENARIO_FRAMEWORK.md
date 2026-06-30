# Scenario Analysis Framework

## Mapping Consensus Data to Scenarios

| Scenario | Probability | Revenue Estimate | EPS Estimate | Price Target |
|----------|------------|-----------------|-------------|-------------|
| Bull | 20-25% | consensus_high | consensus_high | max price target |
| Base | 50-60% | consensus_mean | consensus_mean | avg price target |
| Bear | 20-25% | consensus_low | consensus_low | min price target |

## Probability-Weighted Expected Return

```
E[Return] = P(Bull) × Bull_Upside + P(Base) × Base_Return + P(Bear) × Bear_Downside
```

Where upside/downside = (Price Target - Current Price) / Current Price

## Presentation Table

| Scenario | Probability | Price Target | Return | Revenue Growth | EPS | Key Drivers |
|----------|------------|-------------|--------|---------------|-----|-------------|
| Bull | 25% | $XXX | +XX% | XX% | $X.XX | [Driver 1, Driver 2] |
| Base | 50% | $XXX | +XX% | XX% | $X.XX | [Driver 1, Driver 2] |
| Bear | 25% | $XXX | -XX% | XX% | $X.XX | [Risk 1, Risk 2] |
| **Weighted** | **100%** | **$XXX** | **+XX%** | | | |
