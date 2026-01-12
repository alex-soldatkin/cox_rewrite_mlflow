

WITH
  $baseGraphName AS baseGraph,
  $baseRelTypes AS baseRelTypes,
  $readConcurrency AS readConcurrency,
  -9007199254740991.0 AS MIN_T,
   9007199254740991.0 AS MAX_T

CALL {
  // Real Edges
  MATCH (source:Bank|Company|Person)-[r]->(target:Bank|Company|Person)
  WHERE type(r) IN $baseRelTypes
  RETURN 
    source, 
    target, 
    type(r) AS relType, 
    r.Size AS weight,
    r.temporal_start AS tStart,
    r.temporal_end AS tEnd,
    CASE WHEN type(r) = 'FAMILY' AND coalesce(r.source,'') = 'imputed' THEN 1.0 ELSE 0.0 END AS imputedFlag

  UNION ALL

  // Isolates (Self-Loops with special type)
  MATCH (n:Bank|Company|Person)
  // Optimization: Only include nodes involved in real edges? No, we want ISOLATES.
  // But wait, do we want to double-count nodes involved in edges?
  // GDS Cypher Aggregation takes a stream of relationships.
  // If we emit a self-loop for EVERY node, then EVERY node is projected.
  // Real edges add connections.
  // GDS handles multiple edges fine.
  RETURN 
    n AS source,
    n AS target,
    'ISOLATE' AS relType,
    0.0 AS weight,
    -9007199254740991.0 AS tStart,
    9007199254740991.0 AS tEnd,
    0.0 AS imputedFlag
}
WITH gds.graph.project(
  $baseGraphName,
  source,
  target,
  {
    sourceNodeLabels: labels(source),
    targetNodeLabels: labels(target),

    sourceNodeProperties: {
      tStart: toFloat(coalesce(source.temporal_start, -9007199254740991.0)),
      tEnd:   toFloat(coalesce(source.temporal_end,   9007199254740991.0)),
      is_dead: CASE WHEN coalesce(source.is_dead, false) THEN 1 ELSE 0 END,
      bank_feats: coalesce(source.bank_feats, []),
      network_feats: coalesce(source.network_feats, [])
    },
    targetNodeProperties: {
      tStart: toFloat(coalesce(target.temporal_start, -9007199254740991.0)),
      tEnd:   toFloat(coalesce(target.temporal_end,   9007199254740991.0)),
      is_dead: CASE WHEN coalesce(target.is_dead, false) THEN 1 ELSE 0 END,
      bank_feats: coalesce(target.bank_feats, []),
      network_feats: coalesce(target.network_feats, [])
    },

    relationshipType: relType,
    relationshipProperties: {
      weight: toFloat(coalesce(weight, 1.0)),
      tStart: toFloat(coalesce(tStart, -9007199254740991.0)),
      tEnd:   toFloat(coalesce(tEnd,   9007199254740991.0)),
      imputedFlag: toFloat(imputedFlag)
    }
  },
  { readConcurrency: $readConcurrency }
) AS g
RETURN g.graphName, g.nodeCount, g.relationshipCount, g.projectMillis;
