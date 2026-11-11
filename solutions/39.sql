SELECT b.freelancer_id,count(*) AS completed_count,
count(*) FILTER(WHERE p.completed_at::date>b.proposed_completion_date) AS late_count,
round(avg(p.completed_at::date-b.proposed_completion_date) FILTER(WHERE p.completed_at::date>b.proposed_completion_date),2) AS avg_late_days
FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята' WHERE p.status='завершен' GROUP BY b.freelancer_id;
