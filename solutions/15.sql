SELECT p.customer_id FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята'
JOIN freelancers f ON f.user_id=b.freelancer_id WHERE p.status='завершен' AND f.specialization IN ('Python','Дизайн')
GROUP BY p.customer_id HAVING count(DISTINCT f.specialization)=2;
