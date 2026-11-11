WITH x AS (SELECT f.user_id AS freelancer_id,f.specialization,coalesce(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS revenue
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id,f.specialization)
SELECT freelancer_id,specialization,revenue,coalesce(round(100.0*revenue/nullif(sum(revenue) OVER(PARTITION BY specialization),0),2),0) AS share_pct FROM x;
