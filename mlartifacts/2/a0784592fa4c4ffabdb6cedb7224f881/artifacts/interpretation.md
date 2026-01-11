# Interpretation Report: Model 5: +Topology

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **180.9%**. (** p<0.01)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **36.9%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **28.6%**. (not significant)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **0.6%**. (** p<0.01)
- **network_betweenness**: A one-unit increase decreases the hazard of failure by **0.0%**. (+ p<0.1)
- **network_C_b**: A one-unit increase decreases the hazard of failure by **3.4%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **36.9%** (HR = 0.631)
2. **network_C_b***: Reduces hazard by **3.4%** (HR = 0.966)
3. **network_page_rank***: Reduces hazard by **0.6%** (HR = 0.994)
4. **network_betweenness**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **180.9%** (HR = 2.809)
2. **camel_liquid_assets_ratio**: Increases hazard by **28.6%** (HR = 1.286)
3. **camel_npl_ratio***: Increases hazard by **1.2%** (HR = 1.012)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*