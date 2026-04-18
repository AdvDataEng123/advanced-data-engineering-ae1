-- Top 20 most-cited papers from OpenAlex
-- Uses DISTINCT to dedupe — Lambda fetched the same papers multiple times
SELECT DISTINCT
    title,
    cited_by_count,
    author_names,
    institution_names
FROM openalex
ORDER BY cited_by_count DESC
LIMIT 20;
