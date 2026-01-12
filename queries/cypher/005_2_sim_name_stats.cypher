// ============================================================================
// SIM_NAME Statistics Query
// ============================================================================
// Analyze the created :SIM_NAME relationships.
//
// Run with: bash scripts/run_cypher.sh -f queries/cypher/005_2_sim_name_stats.cypher
// ============================================================================

// Total counts
MATCH ()-[r:SIM_NAME]->()
RETURN 
  count(*) AS total_sim_name_rels,
  sum(r.is_common_surname) AS common_surname_pairs,
  avg(r.lev_dist_last_name) AS avg_surname_sim,
  avg(r.lev_dist_patronymic) AS avg_patronymic_sim,
  count(CASE WHEN r.lev_dist_last_name > 0.88 AND r.lev_dist_patronymic > 0.55 THEN 1 END) AS high_confidence_pairs;
