// Rolling-windows: example per-window metric calls (mutate mode) and export.
//
// This file is a reference for running in Neo4j Browser; the pipeline runs the same
// algorithms via the Python client.
//
// Parameters:
//   $windowGraph: STRING

CALL gds.pageRank.mutate($windowGraph, {
  mutateProperty: 'page_rank',
  relationshipWeightProperty: 'weight',
  maxIterations: 20,
  dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations, didConverge;

CALL gds.degree.mutate($windowGraph, { mutateProperty: 'in_degree', orientation: 'REVERSE' })
YIELD nodePropertiesWritten;

CALL gds.degree.mutate($windowGraph, { mutateProperty: 'out_degree', orientation: 'NATURAL' })
YIELD nodePropertiesWritten;

CALL gds.wcc.mutate($windowGraph, { mutateProperty: 'wcc' })
YIELD componentCount;

CALL gds.louvain.mutate($windowGraph, {
  mutateProperty: 'community_louvain',
  relationshipWeightProperty: 'weight',
  maxIterations: 20,
  includeIntermediateCommunities: true
})
YIELD communityCount, modularity;

CALL gds.fastRP.mutate($windowGraph, {
  mutateProperty: 'fastrp_embedding',
  embeddingDimension: 128,
  iterationWeights: [0.20,0.20,0.20,0.20,0.20],
  nodeSelfInfluence: 0.7,
  randomSeed: 42,
  relationshipWeightProperty: 'weight'
})
YIELD nodePropertiesWritten;

CALL gds.graph.nodeProperties.stream($windowGraph, ['page_rank','in_degree','out_degree','wcc','community_louvain','fastrp_embedding'])
YIELD nodeId, nodeProperty, propertyValue
RETURN nodeId, nodeProperty, propertyValue
LIMIT 25;

