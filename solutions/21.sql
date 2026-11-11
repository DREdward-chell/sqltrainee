WITH x AS (SELECT f.user_id AS freelancer_id,f.specialization,COALESCE(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS revenue
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id,f.specialization)
SELECT freelancer_id,specialization,revenue,dense_rank() OVER(PARTITION BY specialization ORDER BY revenue DESC) AS revenue_rank FROM x;
