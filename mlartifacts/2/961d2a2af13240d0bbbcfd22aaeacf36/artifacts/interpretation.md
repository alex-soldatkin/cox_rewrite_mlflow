# Interpretation Report: Model 1: Controls

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **218.2%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **36.5%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **38.4%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **36.5%** (HR = 0.635)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **218.2%** (HR = 3.182)
2. **camel_liquid_assets_ratio**: Increases hazard by **38.4%** (HR = 1.384)
3. **camel_npl_ratio***: Increases hazard by **1.2%** (HR = 1.012)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*