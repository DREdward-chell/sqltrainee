SELECT p.id AS project_id,p.title FROM projects p WHERE p.budget>50000
AND EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id)
AND NOT EXISTS(SELECT 1 FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id WHERE b.project_id=p.id AND f.hourly_rate<1500);
