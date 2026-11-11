WITH ratings AS (SELECT f.specialization,f.user_id AS freelancer_id,avg(r.rating) AS avg_rating FROM freelancers f
JOIN bids b ON b.freelancer_id=f.user_id AND b.status='принята' JOIN reviews r ON r.project_id=b.project_id GROUP BY f.specialization,f.user_id HAVING count(*)>=2),
x AS (SELECT *,dense_rank() OVER(PARTITION BY specialization ORDER BY avg_rating DESC) AS rn FROM ratings)
SELECT specialization,freelancer_id,round(avg_rating,2) AS avg_rating FROM x WHERE rn=1;
