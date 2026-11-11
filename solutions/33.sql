SELECT a.freelancer_id AS freelancer_id_1,b.freelancer_id AS freelancer_id_2,count(*) AS common_projects FROM bids a JOIN bids b
ON b.project_id=a.project_id AND a.freelancer_id<b.freelancer_id GROUP BY a.freelancer_id,b.freelancer_id HAVING count(*)>=3;
