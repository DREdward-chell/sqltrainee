from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
TASKS=[]
def add(title, text, cols, sql, hint, level=3, ordered=False):
    n=len(TASKS)+1
    TASKS.append(dict(id=n,title=title,text=text,columns=cols.split(),hint=hint,level=level,ordered=ordered))
    (ROOT/f'solutions/{n:02}.sql').write_text(sql.strip()+';\n')

add('Python и заявки за 2023 год',
'''Аналог задания 3. Найдите Python-фрилансеров, подавших строго больше 3 заявок в 2023 году. Одна строка на человека, даже если имена совпадают. Имя и точное количество заявок.''',
'name bid_count', '''SELECT u.name, count(*) AS bid_count FROM users u JOIN freelancers f ON f.user_id=u.id
JOIN bids b ON b.freelancer_id=f.user_id WHERE f.specialization='Python'
AND b.submitted_at >= timestamp '2023-01-01' AND b.submitted_at < timestamp '2024-01-01'
GROUP BY u.id,u.name HAVING count(*)>3''', 'WHERE отбирает строки до группировки, HAVING — группы. Группируй по ID, не только по имени.',2)
add('Только дорогие специалисты',
'''Аналог задания 4. Проекты с бюджетом > 50000, у которых есть хотя бы одна заявка и нет заявок от фрилансеров с hourly_rate < 1500. Ровно 1500 допустимо.''',
'project_id title', '''SELECT p.id AS project_id,p.title FROM projects p WHERE p.budget>50000
AND EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id)
AND NOT EXISTS(SELECT 1 FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id WHERE b.project_id=p.id AND f.hourly_rate<1500)''',
'Нужны две проверки: существование хотя бы одной заявки и отсутствие нарушителя.',3)
add('Среднее по всем проектам',
'''Аналог задания 5. Для каждой имеющейся специализации посчитайте среднее число ее заявок на проект. Знаменатель — ВСЕ проекты базы, включая проекты без заявок этой специализации. Специализации без заявок тоже выводите с 0. Если проектов вообще нет, среднее NULL. Не округляйте.''',
'specialization avg_bids', '''SELECT s.specialization, count(b.id)::numeric/NULLIF((SELECT count(*) FROM projects),0) AS avg_bids
FROM (SELECT DISTINCT specialization FROM freelancers) s LEFT JOIN freelancers f USING(specialization)
LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY s.specialization''',
'Всего заявок специализации / число всех проектов. Не допусти целочисленного деления.',3)
add('Завершенные проекты прошлого месяца',
'''Аналог задания 6. Для специализаций исполнителей проектов, завершенных в прошлом календарном месяце относительно CURRENT_DATE, выведите число проектов и сумму их БЮДЖЕТОВ. Исполнитель определяется принятой заявкой. Специализации без таких проектов не выводите.''',
'specialization project_count total_budget', '''SELECT f.specialization,count(*) AS project_count,sum(p.budget) AS total_budget
FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята' JOIN freelancers f ON f.user_id=b.freelancer_id
WHERE p.status='завершен' AND p.completed_at>=date_trunc('month',CURRENT_DATE)-interval '1 month'
AND p.completed_at<date_trunc('month',CURRENT_DATE) GROUP BY f.specialization''',
'Интервал [начало прошлого месяца, начало текущего). Бюджет проекта отличается от цены заявки.',3)
add('Три прибыльные специализации',
'''Аналог задания 7. Верните ровно три специализации с наибольшей суммой сумм принятых заявок за все время (или меньше, если их меньше трех). Только специализации с принятыми заявками. Сортировка total_amount DESC, при равенстве specialization ASC.''',
'specialization total_amount', '''SELECT f.specialization,sum(b.amount) AS total_amount FROM freelancers f JOIN bids b ON b.freelancer_id=f.user_id
WHERE b.status='принята' GROUP BY f.specialization ORDER BY total_amount DESC,f.specialization ASC LIMIT 3''',
'Сначала агрегирование, потом ORDER BY и LIMIT. Для однозначного топа нужен второй ключ.',3,True)
add('Пары с близкими ценами',
'''Аналог задания 8. Найдите пары фрилансеров с заявками на общий проект, где max(amount) <= min(amount) * 1.10. То есть разница не более 10% МЕНЬШЕЙ цены. Выводите пару ID по возрастанию, один раз за все проекты; проект в результат не включайте.''',
'freelancer_id_1 freelancer_id_2', '''SELECT DISTINCT a.freelancer_id AS freelancer_id_1,b.freelancer_id AS freelancer_id_2
FROM bids a JOIN bids b ON b.project_id=a.project_id AND a.freelancer_id<b.freelancer_id
WHERE greatest(a.amount,b.amount)<=least(a.amount,b.amount)*1.10''',
'Self-join по проекту, a.freelancer_id < b.freelancer_id, затем DISTINCT по паре.',3)
add('Проекты без заявок','Выведите ID и название всех проектов, на которые не поступило ни одной заявки.',
'project_id title', 'SELECT p.id AS project_id,p.title FROM projects p WHERE NOT EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id)',
'NOT EXISTS или LEFT JOIN с проверкой NULL.',2)
add('Количество заявок у каждого фрилансера','Все фрилансеры, включая тех, у кого 0 заявок. Выведите ID, имя и количество заявок.',
'freelancer_id name bid_count','''SELECT f.user_id AS freelancer_id,u.name,count(b.id) AS bid_count FROM freelancers f JOIN users u ON u.id=f.user_id
LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id,u.name''','После LEFT JOIN используй COUNT(b.id), а не COUNT(*).',2)
add('Дешевле собственного среднего','Найдите заявки со стоимостью строго ниже среднего всех заявок того же фрилансера. Выведите ID заявки и ее сумму.',
'bid_id amount','''SELECT b.id AS bid_id,b.amount FROM bids b WHERE b.amount<(SELECT avg(x.amount) FROM bids x WHERE x.freelancer_id=b.freelancer_id)''',
'Коррелированный подзапрос или AVG(...) OVER (PARTITION BY freelancer_id).',2)
add('Экономия на выполненных проектах','Для каждого завершенного проекта выведите бюджет минус сумму принятой заявки. Отрицательная экономия допустима.',
'project_id savings', '''SELECT p.id AS project_id,p.budget-b.amount AS savings FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята' WHERE p.status='завершен' ''',
'Выбери только принятую заявку. Не суммируй остальные ставки.',2)
add('Воронка заказчиков','Для каждого заказчика, включая заказчиков без проектов, выведите число всех, открытых, выполняемых и завершенных проектов.',
'customer_id total_count open_count active_count completed_count', '''SELECT c.user_id AS customer_id,count(p.id) AS total_count,
count(p.id) FILTER(WHERE p.status='открыт') AS open_count,count(p.id) FILTER(WHERE p.status='в работе') AS active_count,
count(p.id) FILTER(WHERE p.status='завершен') AS completed_count FROM customers c LEFT JOIN projects p ON p.customer_id=c.user_id GROUP BY c.user_id''',
'LEFT JOIN и агрегаты с FILTER.',3)
add('Доля принятых заявок','Для каждого фрилансера: количество всех заявок, принятых заявок, процент принятых от всех (0..100), округленный до 2 знаков. При отсутствии заявок процент 0.',
'freelancer_id bid_count accepted_count acceptance_pct','''SELECT f.user_id AS freelancer_id,count(b.id) AS bid_count,
count(b.id) FILTER(WHERE b.status='принята') AS accepted_count,
COALESCE(round(100.0*count(b.id) FILTER(WHERE b.status='принята')/NULLIF(count(b.id),0),2),0) AS acceptance_pct
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id''',
'NULLIF защищает от деления на ноль; COALESCE задает значение для пустой истории.',3)
add('Среднее только по участвовавшим проектам','Для каждой специализации с заявками найдите среднее число ее заявок по тем проектам, где есть хотя бы одна заявка этой специализации. Не округляйте. Сравните смысл с задачей 3.',
'specialization avg_bids','''WITH counts AS (SELECT f.specialization,b.project_id,count(*) AS n FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id GROUP BY f.specialization,b.project_id)
SELECT specialization,avg(n) AS avg_bids FROM counts GROUP BY specialization''',
'Два уровня агрегации: сначала (специализация, проект), потом специализация.',3)
add('Разнообразие участников','Найдите проекты с заявками минимум от трех разных специализаций. Выведите ID и число специализаций.',
'project_id specialization_count','''SELECT b.project_id,count(DISTINCT f.specialization) AS specialization_count FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id
GROUP BY b.project_id HAVING count(DISTINCT f.specialization)>=3''','COUNT(DISTINCT ...), не COUNT(*).',2)
add('Работали с Python и дизайнерами','Заказчики, у которых есть завершенный проект с исполнителем Python и есть завершенный проект с исполнителем Дизайн. Выведите ID заказчика.',
'customer_id','''SELECT p.customer_id FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята'
JOIN freelancers f ON f.user_id=b.freelancer_id WHERE p.status='завершен' AND f.specialization IN ('Python','Дизайн')
GROUP BY p.customer_id HAVING count(DISTINCT f.specialization)=2''','Фильтруй две специализации и проверь, что обе присутствуют.',3)
add('Только Python','Найдите проекты хотя бы с одной заявкой, у которых все участники специализируются на Python.',
'project_id','''SELECT p.id AS project_id FROM projects p WHERE EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id)
AND NOT EXISTS(SELECT 1 FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id WHERE b.project_id=p.id AND f.specialization<>'Python')''',
'«Все» удобно переписать как «не существует нарушителя». Не забудь непустоту.',3)
add('Все заявки дороже бюджета','Проекты с заявками, где каждая предложенная сумма строго больше бюджета проекта.',
'project_id','''SELECT p.id AS project_id FROM projects p JOIN bids b ON b.project_id=p.id GROUP BY p.id,p.budget HAVING min(b.amount)>p.budget''',
'Если минимальная сумма уже больше бюджета, остальные тоже больше.',3)
add('Конкурент дешевле победителя','Выведите ID проектов, где существует отклоненная заявка дешевле принятой. Каждый проект один раз.',
'project_id','''SELECT a.project_id FROM bids a WHERE a.status='принята' AND EXISTS(SELECT 1 FROM bids b WHERE b.project_id=a.project_id AND b.status='отклонена' AND b.amount<a.amount)''',
'Сравнивай заявки одного проекта. EXISTS избавляет от дублирования проекта.',3)
add('Две самые дешевые заявки','В каждом проекте выберите не более двух заявок: amount ASC, при равенстве id ASC. Выведите ID проекта, ID заявки, сумму и номер позиции (1 или 2). Общий порядок строк не важен.',
'project_id bid_id amount position','''WITH x AS (SELECT project_id,id AS bid_id,amount,row_number() OVER(PARTITION BY project_id ORDER BY amount,id) AS position FROM bids)
SELECT project_id,bid_id,amount,position FROM x WHERE position<=2''','ROW_NUMBER дает ровно две строки; RANK при равенстве может дать больше.',3)
add('Два минимальных уровня цен','В каждом проекте найдите заявки, относящиеся к двум наименьшим различным ценам. При равенстве включайте всех. Выведите уровень 1 или 2.',
'project_id bid_id amount price_rank','''WITH x AS (SELECT project_id,id AS bid_id,amount,dense_rank() OVER(PARTITION BY project_id ORDER BY amount) AS price_rank FROM bids)
SELECT project_id,bid_id,amount,price_rank FROM x WHERE price_rank<=2''','DENSE_RANK без пропусков; ID нельзя добавлять в ORDER BY этого окна.',4)
add('Рейтинг доходов внутри специализации','Все фрилансеры, включая без побед. Доход — сумма принятых заявок, иначе 0. Присвойте DENSE_RANK по доходу DESC внутри специализации.',
'freelancer_id specialization revenue revenue_rank','''WITH x AS (SELECT f.user_id AS freelancer_id,f.specialization,COALESCE(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS revenue
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id,f.specialization)
SELECT freelancer_id,specialization,revenue,dense_rank() OVER(PARTITION BY specialization ORDER BY revenue DESC) AS revenue_rank FROM x''',
'Сначала одна строка на фрилансера, затем оконное ранжирование.',4)
add('Накопленный доход','Для каждой принятой заявки выведите ее ID, ID фрилансера, accepted_at и накопленную сумму его принятых заявок. Порядок внутри истории: accepted_at ASC, id ASC.',
'bid_id freelancer_id accepted_at running_revenue','''SELECT id AS bid_id,freelancer_id,accepted_at,sum(amount) OVER(PARTITION BY freelancer_id ORDER BY accepted_at,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue
FROM bids WHERE status='принята' ''','Задай стабильный порядок и ROWS; одинаковые даты не должны схлопываться в одну ступень.',4)
add('Перерыв между заявками','Для каждой заявки выведите ID, ID фрилансера и разницу в целых календарных днях между submitted_at::date текущей и предыдущей заявки этого фрилансера. Порядок submitted_at, id. Для первой заявки gap_days = NULL.',
'bid_id freelancer_id gap_days','''SELECT id AS bid_id,freelancer_id,submitted_at::date-lag(submitted_at::date) OVER(PARTITION BY freelancer_id ORDER BY submitted_at,id) AS gap_days FROM bids''',
'LAG возвращает значение предыдущей строки. Вычитание date дает целое число дней.',4)
add('Последняя заявка каждого','Для фрилансеров с заявками найдите последнюю заявку по submitted_at DESC, id DESC. Выведите freelancer_id, bid_id, submitted_at, amount.',
'freelancer_id bid_id submitted_at amount','''SELECT DISTINCT ON (freelancer_id) freelancer_id,id AS bid_id,submitted_at,amount FROM bids ORDER BY freelancer_id,submitted_at DESC,id DESC''',
'PostgreSQL DISTINCT ON или ROW_NUMBER. При одинаковых датах выигрывает больший ID.',3)
add('Отклонение цены от среднего проекта','Для каждой заявки выведите ее ID, среднюю цену заявок ее проекта и отклонение своей цены от этого среднего. Оба результата округлите до 2 знаков; отклонение считайте от неокругленного среднего.',
'bid_id project_avg difference','''SELECT id AS bid_id,round(avg(amount) OVER(PARTITION BY project_id),2) AS project_avg,
round(amount-avg(amount) OVER(PARTITION BY project_id),2) AS difference FROM bids''',
'Оконный AVG сохраняет одну строку на заявку.',3)
add('Медианная цена','Для каждого проекта с заявками посчитайте непрерывную медиану сумм (для четного количества — среднее двух центральных). Округлите до 2 знаков.',
'project_id median_amount','''SELECT project_id,round((percentile_cont(0.5) WITHIN GROUP(ORDER BY amount))::numeric,2) AS median_amount FROM bids GROUP BY project_id''',
'PERCENTILE_CONT(0.5) WITHIN GROUP.',4)
add('Календарь заявок за 2023 год','Выведите все 12 месяцев 2023 года, даже пустые: month — дата первого дня месяца, bid_count — число поданных заявок. Сортировка month ASC.',
'month bid_count','''SELECT m.month::date AS month,count(b.id) AS bid_count FROM generate_series(timestamp '2023-01-01',timestamp '2023-12-01',interval '1 month') m(month)
LEFT JOIN bids b ON b.submitted_at>=m.month AND b.submitted_at<m.month+interval '1 month' GROUP BY m.month ORDER BY m.month''',
'GENERATE_SERIES создает календарь, LEFT JOIN сохраняет пустые месяцы.',4,True)
add('Месячная выручка и изменение','За последние 6 ПОЛНЫХ месяцев (текущий исключается) выведите month (date), сумму принятых заявок по accepted_at и изменение относительно предыдущего месяца в этом шестимесячном окне. Пустой месяц = 0; первое изменение = NULL. Сортировка month ASC.',
'month revenue delta','''WITH monthly AS (SELECT m.month::date AS month,COALESCE(sum(b.amount),0) AS revenue
FROM generate_series(date_trunc('month',CURRENT_DATE)-interval '6 months',date_trunc('month',CURRENT_DATE)-interval '1 month',interval '1 month') m(month)
LEFT JOIN bids b ON b.status='принята' AND b.accepted_at>=m.month AND b.accepted_at<m.month+interval '1 month' GROUP BY m.month)
SELECT month,revenue,revenue-lag(revenue) OVER(ORDER BY month) AS delta FROM monthly ORDER BY month''',
'Сначала полный календарь с нулями, потом LAG по результату агрегации.',4,True)
add('Скользящее среднее за три месяца','Для 12 месяцев 2023 года выведите month (date), bid_count и среднее количества заявок за текущий и два предыдущих месяца в пределах 2023. Для января окно из 1 месяца, февраля из 2. Округлите среднее до 2 знаков. Сортировка month ASC.',
'month bid_count moving_avg','''WITH monthly AS (SELECT m.month::date AS month,count(b.id) AS bid_count FROM generate_series(timestamp '2023-01-01',timestamp '2023-12-01',interval '1 month') m(month)
LEFT JOIN bids b ON b.submitted_at>=m.month AND b.submitted_at<m.month+interval '1 month' GROUP BY m.month)
SELECT month,bid_count,round(avg(bid_count) OVER(ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS moving_avg FROM monthly ORDER BY month''',
'Нули заполняются ДО применения окна ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.',4,True)
add('Победа с первой попытки','Фрилансеры, у которых самая ранняя заявка по (submitted_at, id) оказалась принятой. Выведите freelancer_id и bid_id этой заявки.',
'freelancer_id bid_id','''WITH x AS (SELECT freelancer_id,id AS bid_id,status,row_number() OVER(PARTITION BY freelancer_id ORDER BY submitted_at,id) AS rn FROM bids)
SELECT freelancer_id,bid_id FROM x WHERE rn=1 AND status='принята' ''',
'Сначала найди первую среди ВСЕХ заявок, затем проверь ее статус.',4)
add('Все открытые проекты заказчика','Найдите пары (customer_id, freelancer_id), где у заказчика есть хотя бы один открытый проект, а фрилансер подал заявку на КАЖДЫЙ открытый проект этого заказчика. Статус заявки любой.',
'customer_id freelancer_id','''SELECT c.user_id AS customer_id,f.user_id AS freelancer_id FROM customers c CROSS JOIN freelancers f
WHERE EXISTS(SELECT 1 FROM projects p WHERE p.customer_id=c.user_id AND p.status='открыт')
AND NOT EXISTS(SELECT 1 FROM projects p WHERE p.customer_id=c.user_id AND p.status='открыт'
AND NOT EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id AND b.freelancer_id=f.user_id))''',
'Реляционное деление: не существует требуемого проекта без заявки этого фрилансера.',5)
add('Одинаковые наборы проектов','Найдите пары разных фрилансеров с одинаковым НЕПУСТЫМ множеством проектов, куда они подавали заявки. ID внутри пары по возрастанию; пара один раз.',
'freelancer_id_1 freelancer_id_2','''SELECT a.user_id AS freelancer_id_1,b.user_id AS freelancer_id_2 FROM freelancers a JOIN freelancers b ON a.user_id<b.user_id
WHERE EXISTS(SELECT 1 FROM bids x WHERE x.freelancer_id=a.user_id)
AND NOT EXISTS((SELECT project_id FROM bids WHERE freelancer_id=a.user_id) EXCEPT (SELECT project_id FROM bids WHERE freelancer_id=b.user_id))
AND NOT EXISTS((SELECT project_id FROM bids WHERE freelancer_id=b.user_id) EXCEPT (SELECT project_id FROM bids WHERE freelancer_id=a.user_id))''',
'Два множества равны, если обе разности пусты. Равенства количества недостаточно.',5)
add('Не менее трех общих проектов','Для каждой пары фрилансеров с минимум тремя общими проектами выведите ID по возрастанию и число общих проектов.',
'freelancer_id_1 freelancer_id_2 common_projects','''SELECT a.freelancer_id AS freelancer_id_1,b.freelancer_id AS freelancer_id_2,count(*) AS common_projects FROM bids a JOIN bids b
ON b.project_id=a.project_id AND a.freelancer_id<b.freelancer_id GROUP BY a.freelancer_id,b.freelancer_id HAVING count(*)>=3''',
'UNIQUE(project_id, freelancer_id) гарантирует одну строку на общий проект после self-join.',4)
add('Единственная самая дешевая заявка','Для каждого проекта найдите заявку, которая строго дешевле ВСЕХ остальных. При равном минимуме проект исключите. Единственная заявка в проекте подходит.',
'project_id bid_id amount','''SELECT b.project_id,b.id AS bid_id,b.amount FROM bids b WHERE NOT EXISTS(SELECT 1 FROM bids x WHERE x.project_id=b.project_id AND x.id<>b.id AND x.amount<=b.amount)''',
'Не должно существовать другой заявки с меньшей ИЛИ равной ценой.',4)
add('Победитель по средней оценке','Для каждой специализации найдите фрилансеров с максимальной средней оценкой при наличии минимум двух отзывов. Включайте всех при равенстве неокругленных средних. Выведите среднюю оценку, округленную до 2 знаков.',
'specialization freelancer_id avg_rating','''WITH ratings AS (SELECT f.specialization,f.user_id AS freelancer_id,avg(r.rating) AS avg_rating FROM freelancers f
JOIN bids b ON b.freelancer_id=f.user_id AND b.status='принята' JOIN reviews r ON r.project_id=b.project_id GROUP BY f.specialization,f.user_id HAVING count(*)>=2),
x AS (SELECT *,dense_rank() OVER(PARTITION BY specialization ORDER BY avg_rating DESC) AS rn FROM ratings)
SELECT specialization,freelancer_id,round(avg_rating,2) AS avg_rating FROM x WHERE rn=1''',
'Не округляй до сравнения и ранжирования.',4)
add('Повторные заказчики','Для пар заказчик–фрилансер с минимум двумя завершенными совместными проектами выведите ID обоих, количество проектов и сумму принятых заявок.',
'customer_id freelancer_id project_count total_amount','''SELECT p.customer_id,b.freelancer_id,count(*) AS project_count,sum(b.amount) AS total_amount FROM projects p
JOIN bids b ON b.project_id=p.id AND b.status='принята' WHERE p.status='завершен' GROUP BY p.customer_id,b.freelancer_id HAVING count(*)>=2''',
'Группа — пара ID, не отдельный проект.',3)
add('Второй различный бюджет','Для каждого заказчика со минимум двумя различными бюджетами проектов выведите второй по величине различный бюджет.',
'customer_id second_budget','''WITH x AS (SELECT customer_id,budget,dense_rank() OVER(PARTITION BY customer_id ORDER BY budget DESC) AS r FROM projects)
SELECT DISTINCT customer_id,budget AS second_budget FROM x WHERE r=2''',
'DENSE_RANK ранжирует различные значения без пропусков.',4)
add('Завершены, но без отзывов','Для каждого заказчика с завершенными проектами выведите количество завершенных проектов, число из них без отзыва и процент без отзыва, округленный до 2 знаков.',
'customer_id completed_count missing_reviews missing_pct','''SELECT p.customer_id,count(*) AS completed_count,count(*) FILTER(WHERE r.project_id IS NULL) AS missing_reviews,
round(100.0*count(*) FILTER(WHERE r.project_id IS NULL)/count(*),2) AS missing_pct FROM projects p LEFT JOIN reviews r ON r.project_id=p.id
WHERE p.status='завершен' GROUP BY p.customer_id''',
'LEFT JOIN на отзывы, фильтр завершенности относится к проекту.',3)
add('Просрочки исполнителей','Для каждого фрилансера с завершенными проектами: число завершенных проектов, число просроченных и среднее число дней просрочки ТОЛЬКО просроченных. Просрочка = completed_at::date > proposed_completion_date. Среднее округлите до 2 знаков; если просрочек нет, NULL.',
'freelancer_id completed_count late_count avg_late_days','''SELECT b.freelancer_id,count(*) AS completed_count,
count(*) FILTER(WHERE p.completed_at::date>b.proposed_completion_date) AS late_count,
round(avg(p.completed_at::date-b.proposed_completion_date) FILTER(WHERE p.completed_at::date>b.proposed_completion_date),2) AS avg_late_days
FROM projects p JOIN bids b ON b.project_id=p.id AND b.status='принята' WHERE p.status='завершен' GROUP BY b.freelancer_id''',
'FILTER внутри AVG исключает непосроченные, а не заменяет их нулями.',4)
add('Выигрыши за месяц после регистрации','Для каждой специализации выведите общее количество фрилансеров и сколько из них имеют хотя бы одну принятую заявку с accepted_at в [registered_at, registered_at + 1 month). Месяц календарный, не 30 суток.',
'specialization freelancer_count early_winners','''SELECT f.specialization,count(*) AS freelancer_count,count(*) FILTER(WHERE EXISTS(SELECT 1 FROM bids b WHERE b.freelancer_id=f.user_id
AND b.status='принята' AND b.accepted_at>=u.registered_at AND b.accepted_at<u.registered_at+interval '1 month')) AS early_winners
FROM freelancers f JOIN users u ON u.id=f.user_id GROUP BY f.specialization''',
'EXISTS не размножает пользователя при нескольких победах.',4)
add('Время ожидания решения','Для каждой специализации с рассмотренными заявками посчитайте среднее время в часах от подачи до принятия/отклонения; поданные без решения исключите. Округлите до 2 знаков.',
'specialization avg_hours','''SELECT f.specialization,round(avg(extract(epoch FROM (coalesce(b.accepted_at,b.rejected_at)-b.submitted_at))/3600),2) AS avg_hours
FROM bids b JOIN freelancers f ON f.user_id=b.freelancer_id WHERE b.status<>'подана' GROUP BY f.specialization''',
'COALESCE объединяет два взаимоисключающих момента решения; EPOCH дает секунды.',3)
add('Серии активных месяцев','По календарю 2023 года для каждого фрилансера найдите максимальную длину серии последовательных месяцев, в каждом из которых была хотя бы одна подача заявки. Фрилансеров без заявок в 2023 выводите с 0.',
'freelancer_id longest_streak','''WITH months AS (SELECT DISTINCT freelancer_id,extract(month FROM submitted_at)::int AS m FROM bids
WHERE submitted_at>=timestamp '2023-01-01' AND submitted_at<timestamp '2024-01-01'),
islands AS (SELECT freelancer_id,m,m-row_number() OVER(PARTITION BY freelancer_id ORDER BY m) AS grp FROM months),
sizes AS (SELECT freelancer_id,grp,count(*) AS n FROM islands GROUP BY freelancer_id,grp)
SELECT f.user_id AS freelancer_id,coalesce(max(s.n),0) AS longest_streak FROM freelancers f LEFT JOIN sizes s ON s.freelancer_id=f.user_id GROUP BY f.user_id''',
'Gaps and islands: для последовательных месяцев (номер месяца - номер строки) постоянно.',5)
add('Пропущенные месяцы между первым и последним','Для каждого фрилансера выведите месяцы 2023 года БЕЗ заявок между его первым и последним активным месяцем в 2023 включительно. month — date первого числа. Без активности в 2023 строк нет.',
'freelancer_id month','''WITH bounds AS (SELECT freelancer_id,date_trunc('month',min(submitted_at)) AS lo,date_trunc('month',max(submitted_at)) AS hi
FROM bids WHERE submitted_at>=timestamp '2023-01-01' AND submitted_at<timestamp '2024-01-01' GROUP BY freelancer_id)
SELECT x.freelancer_id,m.month::date AS month FROM bounds x CROSS JOIN LATERAL generate_series(x.lo,x.hi,interval '1 month') m(month)
WHERE NOT EXISTS(SELECT 1 FROM bids b WHERE b.freelancer_id=x.freelancer_id AND b.submitted_at>=m.month AND b.submitted_at<m.month+interval '1 month')''',
'LATERAL создает свой календарь для каждой строки границ.',5)
add('Доля в доходе специализации','Все фрилансеры: собственный доход от принятых заявок и доля в сумме доходов специализации в процентах (2 знака). При нулевом доходе всей специализации share_pct = 0.',
'freelancer_id specialization revenue share_pct','''WITH x AS (SELECT f.user_id AS freelancer_id,f.specialization,coalesce(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS revenue
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.user_id,f.specialization)
SELECT freelancer_id,specialization,revenue,coalesce(round(100.0*revenue/nullif(sum(revenue) OVER(PARTITION BY specialization),0),2),0) AS share_pct FROM x''',
'Сумму по специализации можно вычислить оконной функцией поверх доходов людей.',4)
add('Минимальный префикс на 80% выручки','Среди фрилансеров с положительным доходом от принятых заявок выберите минимальный префикс списка revenue DESC, freelancer_id ASC, который покрывает не менее 80% общей выручки. Включайте строку, пересекающую порог. Выведите ID, revenue и cumulative_pct (2 знака). Сортировка как в списке.',
'freelancer_id revenue cumulative_pct','''WITH rev AS (SELECT freelancer_id,sum(amount) AS revenue FROM bids WHERE status='принята' GROUP BY freelancer_id),
x AS (SELECT *,sum(revenue) OVER(ORDER BY revenue DESC,freelancer_id ROWS UNBOUNDED PRECEDING) AS running,sum(revenue) OVER() AS total FROM rev)
SELECT freelancer_id,revenue,round(100.0*running/total,2) AS cumulative_pct FROM x
WHERE running-revenue<0.8*total ORDER BY revenue DESC,freelancer_id''',
'Проверяй накопленную сумму ДО текущей строки: она должна быть ниже порога.',5,True)
add('Широкая таблица заявок по статусам','Для каждой специализации, даже без заявок, выведите количество поданных, принятых и отклоненных заявок и сумму принятых (0 при отсутствии).',
'specialization pending_count accepted_count rejected_count accepted_amount','''SELECT f.specialization,count(b.id) FILTER(WHERE b.status='подана') AS pending_count,
count(b.id) FILTER(WHERE b.status='принята') AS accepted_count,count(b.id) FILTER(WHERE b.status='отклонена') AS rejected_count,
coalesce(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS accepted_amount FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id GROUP BY f.specialization''',
'Условные агрегаты и LEFT JOIN.',3)
add('Состав специализаций проекта','Для каждого проекта, включая без заявок, выведите отсортированные по алфавиту уникальные специализации участников, соединенные через запятую и пробел. Для пустого проекта — пустая строка.',
'project_id specializations','''SELECT p.id AS project_id,coalesce(string_agg(DISTINCT f.specialization,', ' ORDER BY f.specialization),'') AS specializations
FROM projects p LEFT JOIN bids b ON b.project_id=p.id LEFT JOIN freelancers f ON f.user_id=b.freelancer_id GROUP BY p.id''',
'STRING_AGG поддерживает DISTINCT и внутренний ORDER BY.',3)
add('Фрилансер выше среднего коллег','Найдите фрилансеров, чей hourly_rate строго больше среднего hourly_rate ДРУГИХ фрилансеров той же специализации. Если коллег нет, исключите. Выведите ID, ставку и среднее коллег, округленное до 2 знаков; сравнивайте до округления.',
'freelancer_id hourly_rate peers_avg','''SELECT f.user_id AS freelancer_id,f.hourly_rate,round(x.a,2) AS peers_avg FROM freelancers f
CROSS JOIN LATERAL (SELECT avg(g.hourly_rate) AS a FROM freelancers g WHERE g.specialization=f.specialization AND g.user_id<>f.user_id) x WHERE f.hourly_rate>x.a''',
'Самого фрилансера нельзя включать в среднее коллег.',4)
add('Минимальная цена и бюджет по заказчикам','Для каждого заказчика выведите число проектов, сумму бюджетов и сумму минимальных предложенных цен по его проектам. Проект без заявок дает 0 в последнюю сумму. Заказчик без проектов: все три показателя 0. Не допускайте умножения бюджетов из-за JOIN.',
'customer_id project_count total_budget total_min_bid','''WITH mins AS (SELECT project_id,min(amount) AS min_amount FROM bids GROUP BY project_id)
SELECT c.user_id AS customer_id,count(p.id) AS project_count,coalesce(sum(p.budget),0) AS total_budget,coalesce(sum(m.min_amount),0) AS total_min_bid
FROM customers c LEFT JOIN projects p ON p.customer_id=c.user_id LEFT JOIN mins m ON m.project_id=p.id GROUP BY c.user_id''',
'Сначала сверни заявки до одной строки на проект. SUM(DISTINCT budget) не исправляет проблему.',4)
add('Сводный отчет без двойного счета','Для каждой специализации выведите число фрилансеров, число всех заявок, число уникальных проектов с заявками, число завершенных проектов ее исполнителей, доход по всем принятым заявкам и средний рейтинг по отзывам выполненных проектов. Специализации без активности включите, числовые счетчики/доход = 0, рейтинг = NULL; рейтинг округлите до 2 знаков.',
'specialization freelancer_count bid_count project_count completed_count revenue avg_rating','''SELECT f.specialization,count(DISTINCT f.user_id) AS freelancer_count,count(b.id) AS bid_count,
count(DISTINCT b.project_id) AS project_count,count(b.id) FILTER(WHERE b.status='принята' AND p.status='завершен') AS completed_count,
coalesce(sum(b.amount) FILTER(WHERE b.status='принята'),0) AS revenue,round(avg(r.rating),2) AS avg_rating
FROM freelancers f LEFT JOIN bids b ON b.freelancer_id=f.user_id LEFT JOIN projects p ON p.id=b.project_id
LEFT JOIN reviews r ON r.project_id=p.id AND b.status='принята' GROUP BY f.specialization''',
'Отзыв относится только к принятой заявке. COUNT(DISTINCT f.user_id) нужен из-за связи один-ко-многим.',5)

assert len(TASKS)==50
(ROOT/'trainer/tasks.json').write_text(json.dumps(TASKS,ensure_ascii=False,indent=2)+'\n')
for t in TASKS:
    f=ROOT/f"answers/{t['id']:02}.sql"
    if not f.exists(): f.write_text(f"-- {t['id']:02}. {t['title']}\n-- Напишите один SELECT или WITH ... SELECT.\n")
print('Created',len(TASKS),'tasks')
