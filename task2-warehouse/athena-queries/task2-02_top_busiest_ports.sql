-- Top 10 busiest border crossing ports by total volume
SELECT
    "port name",
    state,
    SUM(value) AS total
FROM border_crossing
GROUP BY "port name", state
ORDER BY total DESC
LIMIT 10;
