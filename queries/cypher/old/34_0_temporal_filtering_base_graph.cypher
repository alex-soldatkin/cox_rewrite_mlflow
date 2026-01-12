CALL gds.graph.drop('base_temporal', false) YIELD graphName;

:param baseRelTypes => ['OWNERSHIP','MANAGEMENT','FAMILY'];

WITH
  'base_temporal' AS baseGraph,
  $baseRelTypes AS baseRelTypes,
  -9007199254740991.0 AS MIN_T,
   9007199254740991.0 AS MAX_T

MATCH (source:Bank|Company|Person)-[r]->(target:Bank|Company|Person)
WHERE type(r) IN baseRelTypes

WITH gds.graph.project(
  baseGraph,
  source,
  target,
  {
    sourceNodeLabels: labels(source),
    targetNodeLabels: labels(target),

    sourceNodeProperties: {
      tStart: toFloat(coalesce(source.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(source.temporal_end,   MAX_T))
    },
    targetNodeProperties: {
      tStart: toFloat(coalesce(target.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(target.temporal_end,   MAX_T))
    },

    relationshipType: type(r),
    relationshipProperties: {
      weight: toFloat(coalesce(r.Size, 1.0)),
      tStart: toFloat(coalesce(r.temporal_start, MIN_T)),
      tEnd:   toFloat(coalesce(r.temporal_end,   MAX_T)),
      imputedFlag: CASE
        WHEN type(r) = 'FAMILY' AND coalesce(r.source,'') = 'imputed' THEN 1.0
        ELSE 0.0
      END
    }
  },
  { readConcurrency: 4 }
) AS g
RETURN g.graphName, g.nodeCount, g.relationshipCount, g.projectMillis;
