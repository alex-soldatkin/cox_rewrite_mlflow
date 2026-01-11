// Rolling-windows: example filter from 'base_temporal' into a per-window graph.
//
// This file is for reference/debugging in Neo4j Browser; the pipeline uses
// `gds.graph.filter(...)` via the Python client.
//
// Parameters:
//   $windowGraph: STRING
//   $windowStart: INTEGER (epochMillis)
//   $windowEnd:   INTEGER (epochMillis)  // [start, end)
//   $relTypes:    LIST<STRING>
//   $includeImputed01: INTEGER  // 0 exclude imputed FAMILY, 1 include

CALL gds.graph.drop($windowGraph, false) YIELD graphName

WITH
  $windowGraph AS windowGraph,
  toFloat($windowStart) AS start,
  toFloat($windowEnd)   AS end,
  toFloat($includeImputed01) AS includeImputed01,
  $relTypes AS relTypes
WITH
  windowGraph, start, end, includeImputed01, relTypes,
  reduce(pred = '', t IN relTypes |
    pred + CASE WHEN pred = '' THEN '' ELSE ' OR ' END + 'r:' + t
  ) AS relTypePred

CALL gds.graph.filter(
  windowGraph,
  'base_temporal',
  '(n:Bank OR n:Company OR n:Person) AND n.tStart < $end AND n.tEnd > $start',
  '(' + relTypePred + ')
   AND r.tStart < $end AND r.tEnd > $start
   AND (r:FAMILY = FALSE OR $includeImputed01 = 1.0 OR r.imputedFlag = 0.0)',
  { parameters: { start: start, end: end, includeImputed01: includeImputed01 } }
)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis;

