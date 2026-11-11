SELECT a.user_id AS freelancer_id_1,b.user_id AS freelancer_id_2 FROM freelancers a JOIN freelancers b ON a.user_id<b.user_id
WHERE EXISTS(SELECT 1 FROM bids x WHERE x.freelancer_id=a.user_id)
AND NOT EXISTS((SELECT project_id FROM bids WHERE freelancer_id=a.user_id) EXCEPT (SELECT project_id FROM bids WHERE freelancer_id=b.user_id))
AND NOT EXISTS((SELECT project_id FROM bids WHERE freelancer_id=b.user_id) EXCEPT (SELECT project_id FROM bids WHERE freelancer_id=a.user_id));
