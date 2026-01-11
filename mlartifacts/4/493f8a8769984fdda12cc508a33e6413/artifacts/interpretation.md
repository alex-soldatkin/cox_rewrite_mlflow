# Interpretation Report: Model 1: Controls

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **778.0%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.9%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **39.7%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **45.0%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **39.7%** (HR = 0.603)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **778.0%** (HR = 8.780)
2. **camel_liquid_assets_ratio**: Increases hazard by **45.0%** (HR = 1.450)
3. **camel_npl_ratio***: Increases hazard by **1.9%** (HR = 1.019)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*