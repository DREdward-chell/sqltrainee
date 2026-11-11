WITH monthly AS (SELECT m.month::date AS month,COALESCE(sum(b.amount),0) AS revenue
FROM generate_series(date_trunc('month',CURRENT_DATE)-interval '6 months',date_trunc('month',CURRENT_DATE)-interval '1 month',interval '1 month') m(month)
LEFT JOIN bids b ON b.status='принята' AND b.accepted_at>=m.month AND b.accepted_at<m.month+interval '1 month' GROUP BY m.month)
SELECT month,revenue,revenue-lag(revenue) OVER(ORDER BY month) AS delta FROM monthly ORDER BY month;
