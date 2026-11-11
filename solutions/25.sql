SELECT id AS bid_id,round(avg(amount) OVER(PARTITION BY project_id),2) AS project_avg,
round(amount-avg(amount) OVER(PARTITION BY project_id),2) AS difference FROM bids;
