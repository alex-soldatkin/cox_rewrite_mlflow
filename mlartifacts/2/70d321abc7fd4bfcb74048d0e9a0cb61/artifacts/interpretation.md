# Interpretation Report: Model 3: +Foreign

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **213.4%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **36.5%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **36.6%**. (not significant)
- **foreign_FOP_t**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **0.0%**. (** p<0.01)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **36.5%** (HR = 0.635)
2. **foreign_FEC_d***: Reduces hazard by **0.0%** (HR = 1.000)
3. **foreign_FOP_t**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **213.4%** (HR = 3.134)
2. **camel_liquid_assets_ratio**: Increases hazard by **36.6%** (HR = 1.366)
3. **camel_npl_ratio***: Increases hazard by **1.2%** (HR = 1.012)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*