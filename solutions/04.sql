SELECT f.specialization,count(*) AS project_count,sum(p.budget) AS total_budget
FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята' JOIN freelancers f ON f.user_id=b.freelancer_id
WHERE p.status='завершен' AND p.completed_at>=date_trunc('month',CURRENT_DATE)-interval '1 month'
AND p.completed_at<date_trunc('month',CURRENT_DATE) GROUP BY f.specialization;
