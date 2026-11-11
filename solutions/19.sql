WITH x AS (SELECT project_id,id AS bid_id,amount,row_number() OVER(PARTITION BY project_id ORDER BY amount,id) AS position FROM bids)
SELECT project_id,bid_id,amount,position FROM x WHERE position<=2;
