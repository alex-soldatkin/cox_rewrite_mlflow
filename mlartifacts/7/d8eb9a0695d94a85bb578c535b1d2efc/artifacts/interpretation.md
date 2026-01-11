# Interpretation Report: Model 3: Within-Community Network Effects

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_roa**: A one-unit increase decreases the hazard of failure by **13.7%**. (*** p<0.001)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **0.8%**. (not significant)
- **network_out_degree_within**: A one-unit increase decreases the hazard of failure by **26.9%**. (* p<0.05)
- **network_page_rank_within**: A one-unit increase decreases the hazard of failure by **1.2%**. (not significant)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.7%**. (+ p<0.1)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **3.7%**. (** p<0.01)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **2.5%**. (not significant)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **1.2%**. (+ p<0.1)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **network_out_degree_within***: Reduces hazard by **26.9%** (HR = 0.731)
2. **camel_roa***: Reduces hazard by **13.7%** (HR = 0.863)
3. **foreign_FEC_d**: Reduces hazard by **2.5%** (HR = 0.975)
4. **network_page_rank_within**: Reduces hazard by **1.2%** (HR = 0.988)
5. **family_FOP**: Reduces hazard by **1.2%** (HR = 0.988)
6. **family_rho_F**: Reduces hazard by **0.8%** (HR = 0.992)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **3.7%** (HR = 1.037)
2. **camel_npl_ratio**: Increases hazard by **0.7%** (HR = 1.007)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*