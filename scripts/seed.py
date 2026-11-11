"""Воспроизводимые данные: 4 разных набора + пустой набор; даты относительно CURRENT_DATE."""
from datetime import datetime, date, timedelta
from pathlib import Path
import random
import sys
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]

def lit(v):
    if v is None: return 'NULL'
    if isinstance(v,(int,float)): return str(v)
    return "'"+str(v).replace("'","''")+"'"

def generate(schema, seed, today):
    r=random.Random(seed)
    offset=seed*1000 if seed else 0
    uid=lambda n:n+offset
    stmts=[f'CREATE SCHEMA IF NOT EXISTS {schema};', f'SET search_path TO {schema}, pg_catalog;',
           (ROOT/'sql/schema.sql').read_text(), (ROOT/'sql/workflow.sql').read_text()]
    def insert(table,columns,values):
        stmts.append(f'INSERT INTO {table} ({columns}) VALUES ('+', '.join(lit(v) for v in values)+');')
    if schema!='check_empty':
        specs=['Python','Python','Python','Дизайн','Дизайн','SQL','SQL','Копирайтинг','Java','Python','Дизайн','DevOps','DevOps','Java','SQL','Копирайтинг','Python','Дизайн','Go']
        rates=[1500,1499.99,2500,1500,3500,2000,900,700,3000,4200,800,5000,1800,1500,2200,1900,1500,1200,6000]
        for i in range(1,9):
            insert('users','id,name,registered_at',[uid(i),f'Заказчик {i}','2021-01-01'])
            insert('customers','user_id',[uid(i)])
        for i,(spec,rate) in enumerate(zip(specs,rates),101):
            name='Алексей' if i in (101,102) else ['Ирина','Олег','Мария','Анна','Иван','Елена'][i%6]+f' {i}'
            insert('users','id,name,registered_at',[uid(i),name,'2021-02-01'])
            insert('freelancers','user_id,specialization,hourly_rate',[uid(i),spec,rate])
        first=today.replace(day=1)
        previous=(first-timedelta(days=1)).replace(day=1)
        completions=[datetime.combine(previous,datetime.min.time()),
                     datetime.combine(first,datetime.min.time())-timedelta(microseconds=1),
                     datetime.combine(first,datetime.min.time()),
                     datetime.combine(previous,datetime.min.time())-timedelta(microseconds=1)]
        bid_id=0
        for p in range(1,97):
            status='открыт' if p<=24 or p%5==0 else ('в работе' if p%7==0 else 'завершен')
            if p in (26,27,28): status='завершен'
            if p<=20:
                submitted=datetime(2023,1,1)+timedelta(days=(p-1)*17)
                if p==19: submitted=datetime(2022,12,31,23,59,59)
                if p==20: submitted=datetime(2024,1,1)
                created=submitted-timedelta(days=3)
                completed=None
            else:
                if p==29: completed=completions[0]
                elif p in range(25,29): completed=completions[p-25]
                else: completed=datetime.combine(first,datetime.min.time())-timedelta(days=r.randint(1,175),hours=r.randint(0,23))
                submitted=completed-timedelta(days=35)
                created=submitted-timedelta(days=3)
                if status!='завершен': completed=None
            budget=[50000,50000.01,100000,10000,75000,150000,200000][(p+seed)%7]
            # Пустые проекты, ровно один участник, Python с >3 и ровно 3 заявками в 2023.
            if p in (2,10,24,40,60,80,95): participants=[]; status='открыт'; completed=None
            elif p==1: participants=[101,103,104,106]
            elif p==3: participants=[101,102,103]
            elif p in (4,5,6): participants=[101,103,117]
            elif p<19: participants=[101,104,106] if p%2 else [103,105]
            else: participants=r.sample(list(range(101,117)),r.randint(1,9))
            # Для каждого непустого проекта даты заявок совпадают: есть ties для оконных функций.
            winner=r.choice(participants) if participants and status!='открыт' else None
            if p in (26,27,28): status='завершен'; winner=participants[0]
            if p==25: status='открыт'; completed=None; winner=None
            insert('projects','id,customer_id,title,description,budget,status,created_at,completed_at',
                   [uid(p),uid(1+(p%6)),f'Проект {p}','Учебный проект',budget,status,created,completed])
            decision=submitted+timedelta(days=3)
            for j,f in enumerate(participants):
                bid_id+=1
                amount=r.choice([8000,10000,11000,11000.01,12000,50000,75000,100000,150000])
                if p in (1,3,4,5,6): amount=[10000,11000,11000.01,9000][j%4]
                bs='принята' if f==winner else ('отклонена' if winner else 'подана')
                if not winner and p%11==0 and j==0: bs='отклонена'
                insert('bids','id,project_id,freelancer_id,amount,proposed_completion_date,status,submitted_at,accepted_at,rejected_at',
                       [uid(bid_id),uid(p),uid(f),amount,(submitted+timedelta(days=r.choice([15,35,50]))).date(),bs,submitted,
                        decision if bs=='принята' else None,decision if bs=='отклонена' else None])
            if completed and p%3!=0:
                insert('reviews','project_id,rating,comment,created_at',
                       [uid(p),r.choice([1,3,4,5,5]),'' if p%4==0 else 'Работа выполнена',completed+timedelta(days=2)])
        # Непустые равные множества проектов и положительный пример деления.
        for f in (120,121):
            insert('users','id,name,registered_at',[uid(f),f'Тестовый участник {f}','2021-02-01'])
            insert('freelancers','user_id,specialization,hourly_rate',[uid(f),'SQL',1500])
        for p in (97,98):
            insert('projects','id,customer_id,title,budget,created_at',[uid(p),uid(7),f'Общий проект {p}',90000,'2023-01-01'])
            for f in (120,121):
                bid_id+=1
                insert('bids','id,project_id,freelancer_id,amount,proposed_completion_date,submitted_at',
                       [uid(bid_id),uid(p),uid(f),10000,'2023-12-31','2023-02-01' if p==97 else '2023-04-01'])
        # Граница календарного месяца: 31 января + 1 месяц = 28 февраля.
        for f,p,accepted in [(122,99,'2023-02-27'),(123,100,'2023-02-28')]:
            insert('users','id,name,registered_at',[uid(f),f'Новый специалист {f}','2023-01-31'])
            insert('freelancers','user_id,specialization,hourly_rate',[uid(f),'SQL',1600])
            insert('projects','id,customer_id,title,budget,status,created_at,completed_at',
                   [uid(p),uid(7),f'Первый заказ {p}',20000,'завершен','2023-02-01','2023-03-10'])
            bid_id+=1
            insert('bids','id,project_id,freelancer_id,amount,proposed_completion_date,status,submitted_at,accepted_at',
                   [uid(bid_id),uid(p),uid(f),15000,'2023-03-12','принята','2023-02-02',accepted])
        # Смещаем identity sequence после явных ID.
        for table in ['users','projects','bids']:
            stmts.append(f"SELECT setval(pg_get_serial_sequence('{table}','id'), (SELECT max(id) FROM {table}));")
    if schema=='check_3':
        stmts.append('DELETE FROM reviews; DELETE FROM bids; DELETE FROM projects;')
    stmts+=[f'GRANT USAGE ON SCHEMA {schema} TO sqltrainee;',
            f'GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO sqltrainee;',
            f'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {schema} FROM PUBLIC;']
    return '\n'.join(stmts)

if __name__=='__main__':
    today=datetime.now(ZoneInfo('Europe/Moscow')).date()
    out=ROOT/'data/seed.sql'
    out.write_text('\n'.join(generate(s,n,today) for s,n in [('public',0),('check_1',7),('check_2',19),('check_3',43),('check_empty',0)]))
    (ROOT/'data/seed-date.txt').write_text(str(today)+'\n')
    print(out)
