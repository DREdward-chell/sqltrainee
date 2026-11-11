WITH x AS (SELECT customer_id,budget,dense_rank() OVER(PARTITION BY customer_id ORDER BY budget DESC) AS r FROM projects)
SELECT DISTINCT customer_id,budget AS second_budget FROM x WHERE r=2;
