SELECT p.customer_id,b.freelancer_id,count(*) AS project_count,sum(b.amount) AS total_amount FROM projects p
JOIN bids b ON b.project_id=p.id AND b.status='принята' WHERE p.status='завершен' GROUP BY p.customer_id,b.freelancer_id HAVING count(*)>=2;
