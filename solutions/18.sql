SELECT a.project_id FROM bids a WHERE a.status='принята' AND EXISTS(SELECT 1 FROM bids b WHERE b.project_id=a.project_id AND b.status='отклонена' AND b.amount<a.amount);
