# Interpretation Report: Model 2: +Family

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **212.7%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.1%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **36.2%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **37.7%**. (not significant)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **0.3%**. (* p<0.05)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **17.8%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **36.2%** (HR = 0.638)
2. **family_rho_F***: Reduces hazard by **17.8%** (HR = 0.822)
3. **family_FOP***: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **212.7%** (HR = 3.127)
2. **camel_liquid_assets_ratio**: Increases hazard by **37.7%** (HR = 1.377)
3. **camel_npl_ratio***: Increases hazard by **1.1%** (HR = 1.011)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*