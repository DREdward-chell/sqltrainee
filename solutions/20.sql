WITH x AS (SELECT project_id,id AS bid_id,amount,dense_rank() OVER(PARTITION BY project_id ORDER BY amount) AS price_rank FROM bids)
SELECT project_id,bid_id,amount,price_rank FROM x WHERE price_rank<=2;
