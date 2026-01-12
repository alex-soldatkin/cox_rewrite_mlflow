// ============================================================================
// SIM_NAME Relationship Precomputation Query (OPTIMISED)
// ============================================================================
// Creates :SIM_NAME relationships between Person pairs with name similarity data.
// Uses blocking key (first 3 chars of surname) to avoid Cartesian product.
//
// Properties stored:
//   - lev_dist_last_name: Levenshtein similarity of LastName (0.0 to 1.0)
//   - lev_dist_patronymic: Levenshtein similarity of FirstName->MiddleName (0.0 to 1.0)
//   - is_common_surname: 1 if either person has a common Russian surname, 0 otherwise
//
// Run with: bash scripts/run_cypher.sh -f queries/cypher/005_0_precompute_sim_name.cypher
// ============================================================================

// Common surnames flagged with is_common_surname = 1:
// КУЗНЕЦОВ(А), ИВАНОВ(А), ПОПОВ(А), СМИРНОВ(А), ВАСИЛЬЕВ(А), ПЕТРОВ(А),
// КОЗЛОВ(А), МОРОЗОВ(А), НОВИКОВ(А), ВОЛКОВ(А), СОКОЛОВ(А), ПАВЛОВ(А),
// ЛЕБЕДЕВ(А), СЕМЕНОВ(А), ЕГОРОВ(А)

CALL apoc.periodic.iterate(
  // Outer query: iterate over all Person nodes with required name fields
  'MATCH (p1:Person)
   WHERE p1.FirstName IS NOT NULL 
     AND p1.LastName IS NOT NULL 
     AND size(p1.LastName) >= 3
   RETURN p1, left(toUpper(p1.LastName), 3) AS block_key',
  
  // Inner query: find matching candidates within same block
  'CALL (p1, block_key) {
     MATCH (p2:Person)
     WHERE p2.FirstName IS NOT NULL 
       AND p2.LastName IS NOT NULL 
       AND p2.MiddleName IS NOT NULL
       AND size(p2.LastName) >= 3
       AND left(toUpper(p2.LastName), 3) = block_key
       AND elementId(p1) < elementId(p2)
       AND NOT (p1)-[:FAMILY]-(p2)
       AND NOT (p1)-[:SIM_NAME]-(p2)
     WITH p1, p2,
          apoc.text.levenshteinSimilarity(p1.LastName, p2.LastName) AS surname_sim,
          apoc.text.levenshteinSimilarity(p1.FirstName, p2.MiddleName) AS patronymic_sim
     WHERE surname_sim > 0.7 OR patronymic_sim > 0.4
     WITH p1, p2, surname_sim, patronymic_sim,
          CASE WHEN toUpper(p1.LastName) IN [\"КУЗНЕЦОВ\", \"КУЗНЕЦОВА\", \"ИВАНОВ\", \"ИВАНОВА\", \"ПОПОВ\", \"ПОПОВА\", \"СМИРНОВ\", \"СМИРНОВА\", \"ВАСИЛЬЕВ\", \"ВАСИЛЬЕВА\", \"ПЕТРОВ\", \"ПЕТРОВА\", \"КОЗЛОВ\", \"КОЗЛОВА\", \"МОРОЗОВ\", \"МОРОЗОВА\", \"НОВИКОВ\", \"НОВИКОВА\", \"ВОЛКОВ\", \"ВОЛКОВА\", \"СОКОЛОВ\", \"СОКОЛОВА\", \"ПАВЛОВ\", \"ПАВЛОВА\", \"ЛЕБЕДЕВ\", \"ЛЕБЕДЕВА\", \"СЕМЕНОВ\", \"СЕМЕНОВА\", \"ЕГОРОВ\", \"ЕГОРОВА\"]
                    OR toUpper(p2.LastName) IN [\"КУЗНЕЦОВ\", \"КУЗНЕЦОВА\", \"ИВАНОВ\", \"ИВАНОВА\", \"ПОПОВ\", \"ПОПОВА\", \"СМИРНОВ\", \"СМИРНОВА\", \"ВАСИЛЬЕВ\", \"ВАСИЛЬЕВА\", \"ПЕТРОВ\", \"ПЕТРОВА\", \"КОЗЛОВ\", \"КОЗЛОВА\", \"МОРОЗОВ\", \"МОРОЗОВА\", \"НОВИКОВ\", \"НОВИКОВА\", \"ВОЛКОВ\", \"ВОЛКОВА\", \"СОКОЛОВ\", \"СОКОЛОВА\", \"ПАВЛОВ\", \"ПАВЛОВА\", \"ЛЕБЕДЕВ\", \"ЛЕБЕДЕВА\", \"СЕМЕНОВ\", \"СЕМЕНОВА\", \"ЕГОРОВ\", \"ЕГОРОВА\"]
               THEN 1 ELSE 0 END AS is_common
     MERGE (p1)-[r:SIM_NAME]->(p2)
     SET r.lev_dist_last_name = surname_sim,
         r.lev_dist_patronymic = patronymic_sim,
         r.is_common_surname = is_common,
         r.created_at = datetime()
     RETURN count(*) AS created
   }
   RETURN sum(created) AS total_created',
  
  {parallel: false, batchSize: 100}
)
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages;
