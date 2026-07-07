SELECT d.ts,
       d.total_load_actual,
       d.price_actual,
       ROUND(AVG(w.temp), 2)          AS avg_temp_c,
       ROUND(SUM(g.generation_mw), 0) AS total_generation_mw
FROM energy_demand d
LEFT JOIN weather_observations w ON w.ts = d.ts
LEFT JOIN energy_generation   g ON g.ts = d.ts
WHERE d.ts = (SELECT MAX(ts) FROM energy_demand)
GROUP BY d.ts, d.total_load_actual, d.price_actual;

SELECT ts, total_load_actual, price_actual
FROM energy_demand
WHERE ts BETWEEN '2018-06-01 00:00:00+00' AND '2018-06-01 23:00:00+00'
ORDER BY ts
LIMIT 10;

SELECT date_trunc('month', ts) AS month,
       ROUND(AVG(total_load_actual), 0) AS avg_load_mw,
       ROUND(AVG(price_actual), 2)      AS avg_price
FROM energy_demand
GROUP BY month
ORDER BY month
LIMIT 12;

SELECT s.is_renewable,
       ROUND(SUM(g.generation_mw) / 1e6, 2) AS total_twh,
       ROUND(100.0 * SUM(g.generation_mw)
             / SUM(SUM(g.generation_mw)) OVER (), 1) AS pct_of_total
FROM energy_generation g
JOIN generation_sources s ON s.source_id = g.source_id
GROUP BY s.is_renewable
ORDER BY s.is_renewable DESC;

SELECT d.ts,
       d.total_load_actual,
       ROUND(AVG(w.temp), 2)     AS avg_temp_c,
       ROUND(AVG(w.humidity), 0) AS avg_humidity
FROM energy_demand d
JOIN weather_observations w ON w.ts = d.ts
GROUP BY d.ts, d.total_load_actual
ORDER BY d.total_load_actual DESC
LIMIT 5;
