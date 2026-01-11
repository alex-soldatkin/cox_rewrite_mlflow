# Interpretation Report: Model 3: +Foreign

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **601.8%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **45.2%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **41.2%**. (not significant)
- **foreign_FOP_t**: A one-unit increase decreases the odds of failure by **0.0%**. (not significant)
- **foreign_FEC_d**: A one-unit increase decreases the odds of failure by **0.7%**. (** p<0.01)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_roa***: Reduces odds by **45.2%** (OR = 0.548)
3. **camel_liquid_assets_ratio**: Reduces odds by **41.2%** (OR = 0.588)
4. **foreign_FEC_d***: Reduces odds by **0.7%** (OR = 0.993)
5. **foreign_FOP_t**: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **601.8%** (OR = 7.018)
2. **camel_npl_ratio***: Increases odds by **2.2%** (OR = 1.022)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*