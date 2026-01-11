# Interpretation Report: Model 4: +State

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **215.9%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **36.5%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **37.9%**. (not significant)
- **state_SOP**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **state_SCP**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **36.5%** (HR = 0.635)
2. **state_SOP**: Reduces hazard by **0.4%** (HR = 0.996)
3. **state_SCP**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **215.9%** (HR = 3.159)
2. **camel_liquid_assets_ratio**: Increases hazard by **37.9%** (HR = 1.379)
3. **camel_npl_ratio***: Increases hazard by **1.2%** (HR = 1.012)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*