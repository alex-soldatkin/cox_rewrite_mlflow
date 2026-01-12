import os
from graphdatascience import GraphDataScience
from dotenv import load_dotenv

load_dotenv()
neo4j_url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
gds = GraphDataScience(neo4j_url, auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))

print("Debugging Projection Query...")

query = """
CALL {
  // Real Edges
  MATCH (source:Bank|Company|Person)-[r]->(target:Bank|Company|Person)
  WHERE type(r) IN ['OWNERSHIP', 'FAMILY', 'MANAGEMENT']
  RETURN 
    count(r) as count, 'edges' as type

  UNION ALL

  // Isolates (Self-Loops)
  MATCH (n:Bank|Company|Person)
  RETURN 
    count(n) as count, 'isolates' as type
}
RETURN sum(count) as total_rows, collect({type: type, count: count}) as details
"""

res = gds.run_cypher(query)
print(res)
