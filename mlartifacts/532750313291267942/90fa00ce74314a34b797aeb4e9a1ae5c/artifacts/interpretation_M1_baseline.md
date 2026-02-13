# Interpretation: M1: Baseline (no contagion)

## Coefficient Interpretations
Complementary log-log model. Exponentiated coefficients approximate hazard ratios.

- **family_connection_ratio**: HR=0.6496, decreases hazard by 35.0% *** (p=0.0000)
- **family_ownership_pct**: HR=0.9514, decreases hazard by 4.9%  (p=0.3994)
- **state_ownership_pct**: HR=0.8238, decreases hazard by 17.6% + (p=0.0800)
- **foreign_ownership_total_pct**: HR=0.9703, decreases hazard by 3.0%  (p=0.5869)
- **rw_page_rank_4q_lag**: HR=1.1599, increases hazard by 16.0% *** (p=0.0000)
- **rw_out_degree_4q_lag**: HR=0.4670, decreases hazard by 53.3% *** (p=0.0000)
- **camel_roa**: HR=0.9320, decreases hazard by 6.8% *** (p=0.0000)
- **camel_npl_ratio**: HR=1.2582, increases hazard by 25.8% *** (p=0.0000)
- **camel_tier1_capital_ratio**: HR=1.0955, increases hazard by 9.6% *** (p=0.0006)

## Granger Causality Assessment
- FCR coefficient: -0.4315 (p=0.0000)
- **FCR Granger-causes survival** at 5% level