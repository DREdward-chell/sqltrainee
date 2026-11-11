WITH bounds AS (SELECT freelancer_id,date_trunc('month',min(submitted_at)) AS lo,date_trunc('month',max(submitted_at)) AS hi
FROM bids WHERE submitted_at>=timestamp '2023-01-01' AND submitted_at<timestamp '2024-01-01' GROUP BY freelancer_id)
SELECT x.freelancer_id,m.month::date AS month FROM bounds x CROSS JOIN LATERAL generate_series(x.lo,x.hi,interval '1 month') m(month)
WHERE NOT EXISTS(SELECT 1 FROM bids b WHERE b.freelancer_id=x.freelancer_id AND b.submitted_at>=m.month AND b.submitted_at<m.month+interval '1 month');
