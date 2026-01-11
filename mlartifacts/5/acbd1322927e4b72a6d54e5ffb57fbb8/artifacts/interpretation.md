# Interpretation Report: Model 1: Controls

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **835.8%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.1%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **45.1%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **47.0%**. (not significant)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_liquid_assets_ratio**: Reduces odds by **47.0%** (OR = 0.530)
3. **camel_roa***: Reduces odds by **45.1%** (OR = 0.549)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **835.8%** (OR = 9.358)
2. **camel_npl_ratio***: Increases odds by **2.1%** (OR = 1.021)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*