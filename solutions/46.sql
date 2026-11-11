SELECT f.specialization,count(b.id) FILTER(WHERE b.status='подана') AS pending_count,
count(b.id) FILTER(WHERE b.status='принята') AS accepted_count,count(b.id) FILTER(WHERE b.status='отклонена') AS rejected_count,
coalesce(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS accepted_amount FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.specialization;
