WITH x AS (SELECT freelancer_id,id AS bid_id,status,row_number() OVER(PARTITION BY freelancer_id ORDER BY submitted_at,id) AS rn FROM bids)
SELECT freelancer_id,bid_id FROM x WHERE rn=1 AND status='принята';
