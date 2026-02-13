# Interpretation: M4: Pre-2013 (no reverse causality)

## Coefficient Interpretations
Complementary log-log model. Exponentiated coefficients approximate hazard ratios.

- **family_connection_ratio**: HR=0.4148, decreases hazard by 58.5% *** (p=0.0000)
- **family_ownership_pct**: HR=0.8182, decreases hazard by 18.2%  (p=0.1783)
- **state_ownership_pct**: HR=0.0000, decreases hazard by 100.0% * (p=0.0483)
- **foreign_ownership_total_pct**: HR=0.7159, decreases hazard by 28.4%  (p=0.4244)
- **rw_page_rank_4q_lag**: HR=1.0492, increases hazard by 4.9%  (p=0.4416)
- **rw_out_degree_4q_lag**: HR=0.6310, decreases hazard by 36.9% * (p=0.0230)
- **camel_npl_ratio**: HR=1.2317, increases hazard by 23.2% *** (p=0.0000)
- **camel_tier1_capital_ratio**: HR=1.1716, increases hazard by 17.2% *** (p=0.0000)
- **community_failure_lag**: HR=0.9138, decreases hazard by 8.6% * (p=0.0110)

## Granger Causality Assessment
- FCR coefficient: -0.8800 (p=0.0000)
- **FCR Granger-causes survival** at 5% level