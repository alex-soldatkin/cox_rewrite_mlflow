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
    logger.info("Migrating id(n) -> n.gds_id...")
    
    # Set gds_id = id(n)
    query = """
    MATCH (n:Bank|Company|Person)
    SET n.gds_id = id(n)
    RETURN count(n) as updated
    """
    res = gds.run_cypher(query)
    logger.info(f"Updated {res.iloc[0]['updated']} nodes with gds_id.")
    
    logger.info("Migration complete.")

if __name__ == "__main__":
    run_migration()
