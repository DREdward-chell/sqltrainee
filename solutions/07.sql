SELECT p.id AS project_id,p.title FROM projects p WHERE NOT EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id);
