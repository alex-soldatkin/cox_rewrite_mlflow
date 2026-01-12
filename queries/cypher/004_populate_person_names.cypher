// Query to populate FirstName, MiddleName, LastName from full_name
// Russian naming convention: full_name = "LASTNAME FIRSTNAME MIDDLENAME"
// Example: "КОРОЛЕВ АЛЕКСАНДР НИКОЛАЕВИЧ" -> LastName=КОРОЛЕВ, FirstName=АЛЕКСАНДР, MiddleName=НИКОЛАЕВИЧ
//
// This query only updates Person nodes where:
// 1. full_name exists and has exactly 3 space-separated components
// 2. FirstName, MiddleName, or LastName is currently NULL
//
// Run with: bash scripts/run_cypher.sh -f queries/cypher/004_populate_person_names.cypher

MATCH (p:Person)
WHERE p.full_name IS NOT NULL
  AND (p.FirstName IS NULL OR p.MiddleName IS NULL OR p.LastName IS NULL)
WITH p, split(trim(p.full_name), ' ') AS parts
WHERE size(parts) = 3
SET p.LastName = CASE WHEN p.LastName IS NULL THEN parts[0] ELSE p.LastName END,
    p.FirstName = CASE WHEN p.FirstName IS NULL THEN parts[1] ELSE p.FirstName END,
    p.MiddleName = CASE WHEN p.MiddleName IS NULL THEN parts[2] ELSE p.MiddleName END
RETURN count(p) AS updated_count;

// Do the reverse: set full_name from FirstName, MiddleName, LastName

MATCH (p:Person)
WHERE p.full_name is NULL
  AND (p.FirstName IS not NULL AND p.MiddleName IS not NULL AND p.LastName IS not NULL)
SET p.full_name = apoc.text.join([p.LastName, p.FirstName, p.MiddleName], ' ')
RETURN count(p) AS updated_count;
