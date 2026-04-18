-- Yearly border crossings split by border (US-Canada vs US-Mexico)
-- Multi-dimensional aggregation
SELECT
    YEAR(date) AS year,
    border,
    SUM(value) AS total_crossings,
    COUNT(DISTINCT "port name") AS num_ports,
    ROUND(AVG(value), 0) AS avg_per_record
FROM border_crossing
GROUP BY YEAR(date), border
ORDER BY year, border;
