SELECT p.id AS project_id FROM projects p WHERE EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id)
AND NOT EXISTS(SELECT 1 FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id WHERE b.project_id=p.id AND f.specialization<>'Python');
