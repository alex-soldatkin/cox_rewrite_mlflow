# Interpretation Report: Model 4: +State

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **660.7%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **45.3%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **23.5%**. (not significant)
- **state_SOP**: A one-unit increase decreases the odds of failure by **2.6%**. (not significant)
- **state_SCP**: A one-unit increase decreases the odds of failure by **0.0%**. (not significant)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_roa***: Reduces odds by **45.3%** (OR = 0.547)
3. **camel_liquid_assets_ratio**: Reduces odds by **23.5%** (OR = 0.765)
4. **state_SOP**: Reduces odds by **2.6%** (OR = 0.974)
5. **state_SCP**: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **660.7%** (OR = 7.607)
2. **camel_npl_ratio***: Increases odds by **2.2%** (OR = 1.022)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*