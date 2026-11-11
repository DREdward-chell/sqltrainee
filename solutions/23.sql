SELECT id AS bid_id,freelancer_id,submitted_at::date-lag(submitted_at::date) OVER(PARTITION BY freelancer_id ORDER BY submitted_at,id) AS gap_days FROM bids;
