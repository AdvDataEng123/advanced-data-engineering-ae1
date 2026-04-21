-- Task 3: Border crossings summary for OpenSearch export
-- Aggregates crossing data by state, border, and measure type
-- Results exported to S3 then indexed into OpenSearch via Lambda

SELECT
    state,
    border,
    measure,
    SUM(value) AS total_crossings
FROM data_warehouse.border_crossing
GROUP BY state, border, measure
ORDER BY total_crossings DESC;
