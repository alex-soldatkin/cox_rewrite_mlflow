// ============================================================================
// SIM_NAME Cleanup Query  
// ============================================================================
// Deletes all :SIM_NAME relationships. Run before re-computing.
//
// Run with: bash scripts/run_cypher.sh -f queries/cypher/005_1_cleanup_sim_name.cypher
// ============================================================================

CALL apoc.periodic.iterate(
  'MATCH ()-[r:SIM_NAME]->() RETURN r',
  'DELETE r',
  {parallel: true, batchSize: 50000}
)
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages;
