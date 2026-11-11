SELECT s.specialization, count(b.id)::numeric/NULLIF((SELECT count(*) FROM projects),0) AS avg_bids
FROM (SELECT DISTINCT specialization FROM freelancers) s LEFT JOIN freelancers f USING(specialization)
LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY s.specialization;
