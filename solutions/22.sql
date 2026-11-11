SELECT id AS bid_id,freelancer_id,accepted_at,sum(amount) OVER(PARTITION BY freelancer_id ORDER BY accepted_at,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue
FROM bids WHERE status='принята';
