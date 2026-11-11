SELECT DISTINCT a.freelancer_id AS freelancer_id_1,b.freelancer_id AS freelancer_id_2
FROM bids a JOIN bids b ON b.project_id=a.project_id AND a.freelancer_id<b.freelancer_id
WHERE greatest(a.amount,b.amount)<=least(a.amount,b.amount)*1.10;
