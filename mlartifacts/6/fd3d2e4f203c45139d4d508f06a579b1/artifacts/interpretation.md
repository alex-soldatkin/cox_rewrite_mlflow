# Interpretation Report: Model 3: +Network

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_roa**: A one-unit increase decreases the hazard of failure by **9.7%**. (*** p<0.001)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **3.4%**. (*** p<0.001)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **38.4%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.9%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **2.0%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **1.6%**. (* p<0.05)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **network_out_degree***: Reduces hazard by **38.4%** (HR = 0.616)
2. **camel_roa***: Reduces hazard by **9.7%** (HR = 0.903)
3. **family_rho_F***: Reduces hazard by **3.4%** (HR = 0.966)
4. **network_page_rank***: Reduces hazard by **1.6%** (HR = 0.984)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **2.0%** (HR = 1.020)
2. **camel_npl_ratio***: Increases hazard by **0.9%** (HR = 1.009)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*