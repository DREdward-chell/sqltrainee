SELECT b.id AS bid_id,b.amount FROM bids b WHERE b.amount<(SELECT avg(x.amount) FROM bids x WHERE x.freelancer_id=b.freelancer_id);
