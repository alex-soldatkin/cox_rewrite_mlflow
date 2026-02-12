# Interpretation Report: M2: Simple Lagged Network (t-4Q)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **4.0%**. (*** p<0.001)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **5.8%**. (** p<0.01)
- **family_connection_ratio_temporal**: A one-unit increase increases the hazard of failure by **0.7%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **rw_out_degree_4q_lag***: Reduces hazard by **5.8%** (HR = 0.942)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **rw_page_rank_4q_lag***: Increases hazard by **4.0%** (HR = 1.040)
2. **family_connection_ratio_temporal**: Increases hazard by **0.7%** (HR = 1.007)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*