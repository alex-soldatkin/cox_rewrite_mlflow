call apoc.periodic.iterate(
    
'
// FAMILY OWNERSHIP vs DIRECT OWNERSHIP: toy example
// Step 1: First identify the bank
MATCH (bank:Bank)
WHERE NOT bank.is_isolate AND bank.direct_owners IS NULL 
RETURN bank
',

' // Step 2: Find direct owners with a more limited path depth
MATCH (owner)-[:OWNERSHIP]->(bank)
WITH bank, collect(owner) AS direct_owners
// Step 3: Find family connections among direct owners
UNWIND direct_owners AS owner
OPTIONAL MATCH (owner)-[f:FAMILY]-(family_member)
WITH
bank,
owner,
count( DISTINCT family_member) AS family_connections,
direct_owners
// Step 4: Find direct ownership values
MATCH (owner)-[r:OWNERSHIP]->(bank)
WHERE owner IN direct_owners
WITH
bank,
owner,
family_connections,
COALESCE(r.Size, 0) AS ownership_value,
direct_owners
// Step 5: Find family-controlled companies (up to 2 levels)
WITH bank, direct_owners,
sum(CASE WHEN family_connections > 0 THEN ownership_value ELSE 0 END) AS direct_family_owned,
        sum(ownership_value) AS total_direct_owned,
        count(owner) AS direct_owner_count,
        sum(family_connections) AS total_family_connections
// Step 6: Find family control through companies (limited to 2 levels)
OPTIONAL MATCH (family_member)-[:OWNERSHIP*1..4]->(company)-[:OWNERSHIP]->(bank)
WHERE EXISTS((family_member)-[:FAMILY]->())
WITH
    bank,
    direct_family_owned,
    total_direct_owned,
    direct_owner_count,
    total_family_connections,
    count( DISTINCT company) AS family_controlled_companies
// Calculate final properties
WITH
    bank,
    direct_family_owned AS family_direct_ownership_value,
    total_direct_owned AS total_ownership_value,


CASE WHEN total_direct_owned > 0
    THEN 100.0 * direct_family_owned / total_direct_owned
    ELSE 0 END AS family_ownership_percentage,
    direct_owner_count AS direct_owners,
    total_family_connections,
    family_controlled_companies,


CASE WHEN direct_owner_count > 0
THEN toFloat(total_family_connections) / direct_owner_count
ELSE 0 END AS family_connection_ratio
// Step 7: Write properties back to the Bank nodes
 SET bank.family_direct_ownership_value = family_direct_ownership_value,
    bank.total_ownership_value = total_ownership_value,
    bank.family_ownership_percentage = family_ownership_percentage,
    bank.direct_owners = direct_owners,
    bank.total_family_connections = total_family_connections,
    bank.family_controlled_companies = family_controlled_companies,
    bank.family_connection_ratio = family_connection_ratio
// Return the same values as before to show what was written
RETURN
    bank.full_name_cbr AS bank_name,
    bank.bank_regn AS bank_regn,
    bank.family_direct_ownership_value AS family_direct_ownership_value,
    bank.total_ownership_value AS total_ownership_value,
    bank.family_ownership_percentage AS family_ownership_percentage,
    bank.direct_owners AS direct_owners,
    bank.total_family_connections AS total_family_connections,
    bank.family_controlled_companies AS family_controlled_companies,
    bank.family_connection_ratio AS family_connection_ratio;

',

{ batchSize:2, parallel: true }
)
