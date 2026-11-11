SELECT c.user_id AS customer_id,count(p.id) AS total_count,
count(p.id) FILTER(WHERE p.status='открыт') AS open_count,count(p.id) FILTER(WHERE p.status='в работе') AS active_count,
count(p.id) FILTER(WHERE p.status='завершен') AS completed_count FROM customers c LEFT JOIN projects p ON p.customer_id=c.user_id GROUP BY c.user_id;
