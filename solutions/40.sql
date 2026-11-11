SELECT f.specialization,count(*) AS freelancer_count,count(*) FILTER(WHERE EXISTS(SELECT 1 FROM bids b WHERE b.freelancer_id=f.user_id
AND b.status='принята' AND b.accepted_at>=u.registered_at AND b.accepted_at<u.registered_at+interval '1 month')) AS early_winners
FROM freelancers f JOIN users u ON u.id=f.user_id GROUP BY f.specialization;
