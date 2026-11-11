SELECT f.user_id AS freelancer_id,f.hourly_rate,round(x.a,2) AS peers_avg FROM freelancers f
CROSS JOIN LATERAL (SELECT avg(g.hourly_rate) AS a FROM freelancers g WHERE g.specialization=f.specialization AND g.user_id<>f.user_id) x WHERE f.hourly_rate>x.a;
