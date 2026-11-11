SELECT u.name, count(*) AS bid_count FROM users u JOIN freelancers f ON f.user_id=u.id
JOIN bids b ON b.freelancer_id=f.user_id WHERE f.specialization='Python'
AND b.submitted_at >= timestamp '2023-01-01' AND b.submitted_at < timestamp '2024-01-01'
GROUP BY u.id,u.name HAVING count(*)>3;
