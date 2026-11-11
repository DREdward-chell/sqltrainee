SELECT f.user_id AS freelancer_id,u.name,count(b.id) AS bid_count FROM freelancers f JOIN users u ON u.id=f.user_id
LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id,u.name;
