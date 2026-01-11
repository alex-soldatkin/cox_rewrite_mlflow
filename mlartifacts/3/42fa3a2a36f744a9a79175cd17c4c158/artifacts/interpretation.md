# Interpretation Report: Model 2: +Family

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **588.9%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.0%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **44.2%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **24.9%**. (not significant)
- **family_FOP**: A one-unit increase decreases the odds of failure by **0.3%**. (not significant)
- **family_rho_F**: A one-unit increase decreases the odds of failure by **61.4%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **family_rho_F***: Reduces odds by **61.4%** (OR = 0.386)
3. **camel_roa***: Reduces odds by **44.2%** (OR = 0.558)
4. **camel_liquid_assets_ratio**: Reduces odds by **24.9%** (OR = 0.751)
5. **family_FOP**: Reduces odds by **0.3%** (OR = 0.997)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **588.9%** (OR = 6.889)
2. **camel_npl_ratio***: Increases odds by **2.0%** (OR = 1.020)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*