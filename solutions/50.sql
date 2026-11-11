SELECT f.specialization,count(DISTINCT f.user_id) AS freelancer_count,count(b.id) AS bid_count,
count(DISTINCT b.project_id) AS project_count,count(b.id) FILTER(WHERE b.status='принята' AND p.status='завершен') AS completed_count,
coalesce(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS revenue,round(avg(r.rating),2) AS avg_rating
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id LEFT JOIN projects p ON p.id=b.project_id
LEFT JOIN reviews r ON r.project_id=p.id AND b.status='принята' GROUP BY f.specialization;
