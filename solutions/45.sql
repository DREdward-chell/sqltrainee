WITH rev AS (SELECT freelancer_id,sum(amount) AS revenue FROM bids WHERE status='принята' GROUP BY freelancer_id),
x AS (SELECT *,sum(revenue) OVER(ORDER BY revenue DESC,freelancer_id ROWS UNBOUNDED PRECEDING) AS running,sum(revenue) OVER() AS total FROM rev)
SELECT freelancer_id,revenue,round(100.0*running/total,2) AS cumulative_pct FROM x
WHERE running-revenue<0.8*total ORDER BY revenue DESC,freelancer_id;
