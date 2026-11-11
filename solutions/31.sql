SELECT c.user_id AS customer_id,f.user_id AS freelancer_id FROM customers c CROSS JOIN freelancers f
WHERE EXISTS(SELECT 1 FROM projects p WHERE p.customer_id=c.user_id AND p.status='открыт')
AND NOT EXISTS(SELECT 1 FROM projects p WHERE p.customer_id=c.user_id AND p.status='открыт'
AND NOT EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id AND b.freelancer_id=f.user_id));
