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
    logger.info("Migrating imputed_flag property...")
    
    # 1. FAMILY edges
    # Check current state
    logger.info("Setting imputed_flag for FAMILY edges...")
    query = """
    MATCH ()-[r:FAMILY]->()
    SET r.imputed_flag = CASE 
        WHEN coalesce(r.source, '') = 'imputed' THEN 1.0 
        ELSE 0.0 
    END
    RETURN count(r) as updated
    """
    res = gds.run_cypher(query)
    logger.info(f"Updated {res.iloc[0]['updated']} FAMILY edges.")

    # 2. Other types (OWNERSHIP, MANAGEMENT) - default to 0.0
    # Actually, if we use defaultValue=0.0 in projection, we don't need to check other types.
    # But setting it is cleaner.
    logger.info("Setting imputed_flag for OWNERSHIP/MANAGEMENT...")
    query_others = """
    MATCH ()-[r:OWNERSHIP|MANAGEMENT]->()
    SET r.imputed_flag = 0.0
    RETURN count(r) as updated
    """
    res_others = gds.run_cypher(query_others)
    logger.info(f"Updated {res_others.iloc[0]['updated']} other edges.")
    
    logger.info("Migration complete.")

if __name__ == "__main__":
    run_migration()
