-- Border crossings by year (trend over time)
SELECT
    YEAR(date) AS year,
    SUM(value) AS total_crossings
FROM border_crossing
GROUP BY YEAR(date)
ORDER BY year;
