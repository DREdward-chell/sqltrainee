SELECT p.id AS project_id,coalesce(string_agg(DISTINCT f.specialization,', ' ORDER BY f.specialization),'') AS specializations
FROM projects p LEFT JOIN bids b ON b.project_id=p.id LEFT JOIN freelancers f ON f.user_id=b.freelancer_id GROUP BY p.id;
