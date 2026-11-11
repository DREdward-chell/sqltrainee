SELECT DISTINCT ON (freelancer_id) freelancer_id,id AS bid_id,submitted_at,amount FROM bids ORDER BY freelancer_id,submitted_at DESC,id DESC;
