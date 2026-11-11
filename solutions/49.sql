WITH mins AS (SELECT project_id,min(amount) AS min_amount FROM bids GROUP BY project_id)
SELECT c.user_id AS customer_id,count(p.id) AS project_count,coalesce(sum(p.budget),0) AS total_budget,coalesce(sum(m.min_amount),0) AS total_min_bid
FROM customers c LEFT JOIN projects p ON p.customer_id=c.user_id LEFT JOIN mins m ON m.project_id=p.id GROUP BY c.user_id;
