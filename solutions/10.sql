SELECT p.id AS project_id,p.budget-b.amount AS savings FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята' WHERE p.status='завершен';
