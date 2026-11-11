WITH monthly AS (SELECT m.month::date AS month,count(b.id) AS bid_count FROM generate_series(timestamp '2023-01-01',timestamp '2023-12-01',interval '1 month') m(month)
LEFT JOIN bids b ON b.submitted_at>=m.month AND b.submitted_at<m.month+interval '1 month' GROUP BY m.month)
SELECT month,bid_count,round(avg(bid_count) OVER(ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS moving_avg FROM monthly ORDER BY month;
