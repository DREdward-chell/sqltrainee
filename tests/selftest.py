"""Проверка эталонов, независимые Python-оракулы, ошибочные решения и бизнес-ограничения."""
from collections import Counter,defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trainer import TASKS, compare, check
from trainer.db import Connection, DatabaseError, ROOT, SCHEMAS, query

def records(table,schema):
    cols,rows=query('SELECT * FROM '+table,schema)
    return [dict(zip(cols,r)) for r in rows]

def oracle(schema):
    users={u['id']:u for u in records('users',schema)}
    fs={f['user_id']:f for f in records('freelancers',schema)}
    ps={p['id']:p for p in records('projects',schema)}
    bids=records('bids',schema)
    by_project=defaultdict(list)
    for b in bids: by_project[b['project_id']].append(b)
    today=datetime.fromisoformat(query('SELECT CURRENT_DATE::text',schema)[1][0][0])
    upper=today.replace(day=1); lower=(upper-timedelta(days=1)).replace(day=1)
    counts=Counter(b['freelancer_id'] for b in bids if '2023-01-01'<=b['submitted_at']<'2024-01-01')
    answers={1:[(users[f]['name'],n) for f,n in counts.items() if fs[f]['specialization']=='Python' and n>3]}
    answers[2]=[(p['id'],p['title']) for p in ps.values() if p['budget']>50000 and by_project[p['id']]
                and all(fs[b['freelancer_id']]['hourly_rate']>=1500 for b in by_project[p['id']])]
    scount=Counter(fs[b['freelancer_id']]['specialization'] for b in bids)
    answers[3]=[(s,Decimal(scount[s])/len(ps) if ps else None) for s in {f['specialization'] for f in fs.values()}]
    report=defaultdict(lambda:[0,Decimal(0)])
    revenue=defaultdict(Decimal)
    for b in bids:
        if b['status']!='принята': continue
        s=fs[b['freelancer_id']]['specialization']; revenue[s]+=b['amount']; p=ps[b['project_id']]
        if p['status']=='завершен' and lower<=datetime.fromisoformat(p['completed_at'])<upper:
            report[s][0]+=1; report[s][1]+=p['budget']
    answers[4]=[(s,*vals) for s,vals in report.items()]
    answers[5]=sorted(revenue.items(),key=lambda x:(-x[1],x[0]))[:3]
    pairs=set()
    for bs in by_project.values():
        for a in bs:
            for b in bs:
                if a['freelancer_id']<b['freelancer_id'] and max(a['amount'],b['amount'])<=min(a['amount'],b['amount'])*Decimal('1.10'):
                    pairs.add((a['freelancer_id'],b['freelancer_id']))
    answers[6]=list(pairs)
    return answers

def run():
    n=0
    for schema in SCHEMAS:
        for t in TASKS:
            result=query((ROOT/f"solutions/{t['id']:02}.sql").read_text(),schema)
            assert result[0]==t['columns'],(t['id'],result[0],t['columns'])
            n+=1
        for tid,rows in oracle(schema).items():
            actual=query((ROOT/f'solutions/{tid:02}.sql').read_text(),schema)
            ok,message=compare((TASKS[tid-1]['columns'],rows),actual,TASKS[tid-1]['ordered'])
            assert ok,(schema,tid,message)
    print(f'PASS: {n} запусков эталонов; 30 независимых Python-проверок исходных шести задач.')
    # Проверяем всю цепочку checker; прогресс пользователя не изменяем.
    for tid in (1,3,4,5,6,19,27,32,45,50):
        assert check(tid,(ROOT/f'solutions/{tid:02}.sql').read_text(),save=False)
    print('PASS: checker принимает 10 эталонов на всех наборах.')
    mutants={
       1:("GROUP BY u.id,u.name", "GROUP BY u.name"),
       2:("AND EXISTS(SELECT 1 FROM bids b WHERE b.project_id=p.id)",""),
       3:("(SELECT count(*) FROM projects)","(SELECT count(DISTINCT project_id) FROM bids)"),
       4:("sum(p.budget)","sum(b.amount)"),
       6:("least(a.amount,b.amount)*1.10","greatest(a.amount,b.amount)*1.10"),
       8:("count(b.id)","count(*)"),
       19:("row_number() OVER(PARTITION BY project_id ORDER BY amount,id)","dense_rank() OVER(PARTITION BY project_id ORDER BY amount)"),
       20:("dense_rank()","row_number()"),
       34:("x.amount<=b.amount","x.amount<b.amount"),
       40:("interval '1 month'","interval '30 days'"),
       49:("sum(p.budget)","sum(DISTINCT p.budget)"),
       50:("AND b.status='принята' GROUP BY","GROUP BY")}
    for tid,(a,b) in mutants.items():
        source=(ROOT/f'solutions/{tid:02}.sql').read_text()
        assert a in source,(tid,a)
        assert not check(tid,source.replace(a,b),save=False),(tid,'Ошибочное решение принято')
    # Нарушение даты, дубликаты и неверный порядок проверяются отдельно.
    assert not compare((['x'],[(1,),(1,)]),(['x'],[(1,)]))[0]
    assert not compare((['x'],[(1,),(2,)]),(['x'],[(2,),(1,)]),True)[0]
    assert compare((['x'],[(1,),(2,)]),(['x'],[(2,),(1,)]))[0]
    assert not compare((['x'],[(None,)]),(['x'],[(0,)]))[0]
    assert not compare((['x'],[(True,)]),(['x'],[(1,)]))[0]
    print(f'PASS: {len(mutants)} типовых ошибок отклоняются; сравнение учитывает NULL, дубликаты и порядок.')
    for statement in ('DELETE FROM bids','SELECT 1; SELECT 2','CREATE TABLE forbidden(id int)'):
        try: query(statement)
        except DatabaseError: pass
        else: raise AssertionError('Запрещенный запрос прошел: '+statement)
    print('PASS: ответы не могут менять данные; несколько SQL-операторов отклоняются.')
    with Connection(admin=True) as c:
        def fails(statement):
            c.execute('BEGIN')
            try:
                c.execute(statement); c.execute('SET CONSTRAINTS ALL IMMEDIATE')
            except DatabaseError:
                c.execute('ROLLBACK'); return
            c.execute('ROLLBACK'); raise AssertionError('Ожидалось ограничение: '+statement)
        fails("UPDATE bids SET amount=0 WHERE id=1")
        fails("UPDATE freelancers SET hourly_rate=NULL WHERE user_id=101")
        fails("INSERT INTO bids(project_id,freelancer_id,amount,proposed_completion_date,submitted_at) VALUES(1,101,100,'2024-01-01','2023-01-01')")
        fails("INSERT INTO reviews(project_id,rating,comment) VALUES(1,5,'Рано')")
        fails("UPDATE projects SET status='в работе' WHERE id=2")
        fails("DELETE FROM bids WHERE status='принята' AND project_id=26")
        fails("INSERT INTO bids(project_id,freelancer_id,amount,proposed_completion_date,submitted_at) VALUES(2,999999,100,'2024-01-01','2023-01-01')")
        fails("UPDATE bids SET project_id=2 WHERE status='принята' AND project_id=26")
        c.execute('BEGIN')
        try:
            c.execute("SELECT choose_bid(1, timestamp '2023-01-10')")
            c.execute('SET CONSTRAINTS ALL IMMEDIATE')
            assert c.execute('SELECT status FROM projects WHERE id=1')[1]==[('в работе',)]
            assert c.execute("SELECT count(*) FROM bids WHERE project_id=1 AND status='принята'")[1]==[(1,)]
            assert c.execute("SELECT count(*) FROM bids WHERE project_id=1 AND status='подана'")[1]==[(0,)]
            c.execute("SELECT complete_project(1,timestamp '2023-01-20')")
            c.execute("INSERT INTO reviews(project_id,rating,comment,created_at) VALUES(1,5,'OK','2023-01-21')")
            c.execute('SET CONSTRAINTS ALL IMMEDIATE')
        finally: c.execute('ROLLBACK')
    print('PASS: 8 проверок ограничений и полный цикл выбора → завершения → отзыва (с откатом).')
    print('SELFTEST PASSED')
if __name__=='__main__': run()
