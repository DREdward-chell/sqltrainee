WITH months AS (SELECT DISTINCT freelancer_id,extract(month FROM submitted_at)::int AS m FROM bids
WHERE submitted_at>=timestamp '2023-01-01' AND submitted_at<timestamp '2024-01-01'),
islands AS (SELECT freelancer_id,m,m-row_number() OVER(PARTITION BY freelancer_id ORDER BY m) AS grp FROM months),
sizes AS (SELECT freelancer_id,grp,count(*) AS n FROM islands GROUP BY freelancer_id,grp)
SELECT f.user_id AS freelancer_id,coalesce(max(s.n),0) AS longest_streak FROM freelancers f LEFT JOIN sizes s ON s.freelancer_id=f.user_id GROUP BY f.user_id;
