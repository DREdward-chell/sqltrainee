SELECT project_id,round((percentile_cont(0.5) WITHIN GROUP(ORDER BY amount))::numeric,2) AS median_amount FROM bids GROUP BY project_id;
