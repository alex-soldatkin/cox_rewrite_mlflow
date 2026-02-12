# Interpretation Report: M2: + Bank Controls

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio_temporal_lag**: A one-unit increase increases the hazard of failure by **1.2%**. (not significant)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **6.7%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **2.4%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **4.5%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **6.7%** (HR = 0.933)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **4.5%** (HR = 1.045)
2. **camel_npl_ratio***: Increases hazard by **2.4%** (HR = 1.024)
3. **family_connection_ratio_temporal_lag**: Increases hazard by **1.2%** (HR = 1.012)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*