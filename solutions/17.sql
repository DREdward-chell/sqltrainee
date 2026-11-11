SELECT p.id AS project_id FROM projects p JOIN bids b ON b.project_id=p.id GROUP BY p.id,p.budget HAVING min(b.amount)>p.budget;
