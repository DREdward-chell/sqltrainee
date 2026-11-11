SELECT b.project_id,b.id AS bid_id,b.amount FROM bids b WHERE NOT EXISTS(SELECT 1 FROM bids x WHERE x.project_id=b.project_id AND x.id<>b.id AND x.amount<=b.amount);
