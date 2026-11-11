SELECT f.specialization,sum(b.amount) AS total_amount FROM freelancers f JOIN bids b ON b.freelancer_id=f.user_id
WHERE b.status='принята' GROUP BY f.specialization ORDER BY total_amount DESC,f.specialization ASC LIMIT 3;
