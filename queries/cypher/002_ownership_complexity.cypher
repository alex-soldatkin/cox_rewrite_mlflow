// Calculate weighted ownership complexity based on both depth and dispersion
MATCH path = (owner)-[:OWNERSHIP*1..5]->(bank:Bank {bank_regn: "912"})
WITH 
    bank,
    count(DISTINCT owner) AS unique_owners,
    avg(length(path)) AS avg_path_length,
    count(path) AS total_paths
RETURN 
    bank.full_name_cbr AS bank_name,
    unique_owners,
    avg_path_length,
    total_paths,
    avg_path_length * log10(1 + unique_owners) AS complexity_score