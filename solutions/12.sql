SELECT f.user_id AS freelancer_id,count(b.id) AS bid_count,
count(b.id) FILTER(WHERE b.status='принята') AS accepted_count,
COALESCE(round(100.0*count(b.id) FILTER(WHERE b.status='принята')/NULLIF(count(b.id),0),2),0) AS acceptance_pct
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id;
