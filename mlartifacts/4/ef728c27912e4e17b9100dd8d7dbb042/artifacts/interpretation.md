# Interpretation Report: Model 3: +Family

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **520.1%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.8%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **39.5%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **17.2%**. (not significant)
- **network_in_degree**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **25.9%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **2.0%**. (** p<0.01)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **58.2%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **family_rho_F***: Reduces hazard by **58.2%** (HR = 0.418)
2. **camel_roa***: Reduces hazard by **39.5%** (HR = 0.605)
3. **network_out_degree***: Reduces hazard by **25.9%** (HR = 0.741)
4. **network_page_rank***: Reduces hazard by **2.0%** (HR = 0.980)
5. **family_FOP**: Reduces hazard by **0.4%** (HR = 0.996)
6. **network_in_degree**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **520.1%** (HR = 6.201)
2. **camel_liquid_assets_ratio**: Increases hazard by **17.2%** (HR = 1.172)
3. **camel_npl_ratio***: Increases hazard by **1.8%** (HR = 1.018)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*