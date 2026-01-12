import os
import logging
from graphdatascience import GraphDataScience
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

load_dotenv()
neo4j_url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
gds = GraphDataScience(neo4j_url, auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))

def run_migration():
    logger.info("Migrating is_dead -> is_dead_int...")
    
    # Set is_dead_int = 1 where is_dead is true
    # We don't strictly need to set 0 if we use defaultValue=0.0 in projection.
    # But setting 0 for explicit falses is good.
    
    query = """
    MATCH (n:Bank|Company|Person)
    SET n.is_dead_int = CASE WHEN coalesce(n.is_dead, false) THEN 1 ELSE 0 END
    RETURN count(n) as updated
    """
    res = gds.run_cypher(query)
    logger.info(f"Updated {res.iloc[0]['updated']} nodes with is_dead_int.")
    
    logger.info("Migration complete.")

if __name__ == "__main__":
    run_migration()
