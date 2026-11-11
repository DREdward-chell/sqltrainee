SELECT f.specialization,round(avg(extract(epoch FROM (coalesce(b.accepted_at,b.rejected_at)-b.submitted_at))/3600),2) AS avg_hours
FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id WHERE b.status<>'подана' GROUP BY f.specialization;
