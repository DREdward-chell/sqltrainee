SELECT b.project_id,count(DISTINCT f.specialization) AS specialization_count FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id
GROUP BY b.project_id HAVING count(DISTINCT f.specialization)>=3;
