MATCH (bank:Bank)
WHERE NOT bank.is_isolate
WITH bank
// Step 2: Find direct owners with a more limited path depth
MATCH (owner)-[:OWNERSHIP]->(bank)
WITH bank, collect(owner) AS direct_owners
// Step 3: Find family connections among direct owners
UNWIND direct_owners AS owner
OPTIONAL MATCH (owner)-[f:FAMILY]-(family_member)
WITH
  bank,
  owner,
  count(DISTINCT family_member) AS family_connections,
  direct_owners
// Step 4: Find direct ownership values
MATCH (owner)-[r:OWNERSHIP]->(bank)
WHERE owner IN direct_owners
WITH
  bank, owner, family_connections, COALESCE(r.FaceValue, r.Size, 0) AS ownership_value, direct_owners
// Step 5: Find family-controlled companies (up to 4 levels)
WITH bank, direct_owners,
  sum(
    CASE WHEN family_connections > 0 
         THEN ownership_value 
         ELSE 0 
    END
  ) AS direct_family_owned,
  sum(ownership_value) AS total_direct_owned,
  count(owner) AS direct_owner_count,
  sum(family_connections) AS total_family_connections
// Step 6: Find family control through companies (limited to 4 levels)
OPTIONAL MATCH (family_member)-[:OWNERSHIP*1..4]->(company)-[:OWNERSHIP]->(bank)
WHERE EXISTS((family_member)-[:FAMILY]->())
WITH bank, direct_family_owned, total_direct_owned, direct_owner_count, total_family_connections, count(DISTINCT company) AS family_controlled_companies
RETURN bank.Name AS bank_name, bank.bank_regn AS bank_regn, direct_family_owned AS family_direct_ownership_value, total_direct_owned AS total_ownership_value,
  CASE WHEN total_direct_owned > 0
       THEN 100.0 * direct_family_owned / total_direct_owned
       ELSE 0 
  END AS family_ownership_percentage,
  direct_owner_count AS direct_owners, total_family_connections, family_controlled_companies,
  CASE WHEN direct_owner_count > 0
       THEN toFloat(total_family_connections) / direct_owner_count
       ELSE 0 
  END AS family_connection_ratio;