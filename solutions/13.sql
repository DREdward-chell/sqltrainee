WITH counts AS (SELECT f.specialization,b.project_id,count(*) AS n FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id GROUP BY f.specialization,b.project_id)
SELECT specialization,avg(n) AS avg_bids FROM counts GROUP BY specialization;
