SELECT p.customer_id,count(*) AS completed_count,count(*) FILTER(WHERE r.project_id IS NULL) AS missing_reviews,
round(100.0*count(*) FILTER(WHERE r.project_id IS NULL)/count(*),2) AS missing_pct FROM projects p LEFT JOIN reviews r ON r.project_id=p.id
WHERE p.status='завершен' GROUP BY p.customer_id;
