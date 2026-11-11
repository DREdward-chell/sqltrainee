"""SQL-тренажёр. В notebook: from trainer import *; install()"""
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path
from datetime import datetime
import json
import re
from .db import ROOT, SCHEMAS, DatabaseError, query

TASKS=json.loads((ROOT/'trainer/tasks.json').read_text())

def task(number):
    if not 1<=int(number)<=len(TASKS): raise ValueError('Номер задачи: 1..50')
    return TASKS[int(number)-1]

def show_task(number):
    t=task(number)
    print(f"{t['id']:02}. {t['title']}  •  сложность {t['level']}/5\n\n{t['text']}\n\nКолонки: {', '.join(t['columns'])}")
    print('Порядок строк: '+('проверяется согласно условию' if t['ordered'] else 'не важен; дубликаты учитываются'))

def hint(number):
    print(task(number)['hint'])

def solution(number):
    """Показывается только при явном вызове; не запускает и не отмечает задачу решенной."""
    task(number)
    print((ROOT/f'solutions/{int(number):02}.sql').read_text())

def _canonical(value):
    if isinstance(value,bool): return ('boolean',value)
    if isinstance(value,(int,float,Decimal)):
        return ('number',Decimal(str(value)).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP))
    return ('null',) if value is None else ('text',str(value))

def compare(expected,actual,ordered=False):
    ec,er=expected; ac,ar=actual
    if ec!=ac: return False,f"Колонки: ожидались {ec}, получены {ac}. Проверь AS и порядок колонок."
    e=[tuple(_canonical(v) for v in row) for row in er]
    a=[tuple(_canonical(v) for v in row) for row in ar]
    if (e==a if ordered else Counter(e)==Counter(a)): return True,'OK'
    missing=list((Counter(e)-Counter(a)).elements())
    extra=list((Counter(a)-Counter(e)).elements())
    def readable(rows):
        return [tuple(None if v[0]=='null' else str(v[1]) for v in row) for row in rows[:3]]
    msg=f'Ожидалось строк: {len(er)}, получено: {len(ar)}.'
    if not missing and not extra: msg+=' Значения верны, но неверен порядок строк.'
    if missing: msg+='\nНе хватает (до 3 строк): '+repr(readable(missing))
    if extra: msg+='\nЛишние (до 3 строк): '+repr(readable(extra))
    return False,msg

@dataclass
class CheckResult:
    number: int
    passed: bool
    passed_sets: int
    total_sets: int
    message: str
    def __bool__(self): return self.passed
    def __repr__(self): return ('✓' if self.passed else '✗')+f' Задача {self.number:02}: {self.passed_sets}/{self.total_sets} наборов.\n'+self.message
    def _repr_html_(self):
        color='#166534' if self.passed else '#b91c1c'
        return f'<div style="border-left:4px solid {color};padding:12px 16px;background:#f8fafc;color:#172033"><strong>{escape(repr(self).split(chr(10))[0])}</strong><pre style="white-space:pre-wrap">{escape(self.message)}</pre></div>'

def _save_progress(number,passed,sets):
    path=ROOT/'progress.json'
    try: state=json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError): state={}
    previous=state.get(str(number),{})
    state[str(number)]={'passed':passed,'passed_sets':sets,'attempts':previous.get('attempts',0)+1,'updated_at':datetime.now().isoformat(timespec='seconds')}
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)); tmp.replace(path)

def check(number,sql,*,save=True):
    """Сравнивает с эталоном на всех пяти схемах, сохраняет ответ в answers/NN.sql."""
    t=task(number); number=t['id']
    # Пустые заготовки можно запускать через Run All без потока ошибок.
    if not re.sub(r'--[^\n]*','',sql).strip():
        return CheckResult(number,False,0,len(SCHEMAS),'Пока пусто. Напиши запрос под %%check.')
    if save: (ROOT/f'answers/{number:02}.sql').write_text(sql.strip()+'\n')
    reference=(ROOT/f'solutions/{number:02}.sql').read_text()
    failures=[]; passed=0
    for schema in SCHEMAS:
        try:
            expected=query(reference,schema)
        except DatabaseError as exc:
            return CheckResult(number,False,passed,len(SCHEMAS),'Ошибка среды/эталона: '+str(exc))
        try:
            actual=query(sql,schema)
            ok,message=compare(expected,actual,t['ordered'])
        except DatabaseError as exc:
            ok=False; message='Ошибка SQL:\n'+str(exc)
        if ok: passed+=1
        else: failures.append(f'Набор {schema}: {message}')
    success=passed==len(SCHEMAS)
    if save: _save_progress(number,success,passed)
    message='Верно на всех наборах. Можно переходить дальше.' if success else '\n\n'.join(failures[:2])
    if len(failures)>2: message+=f'\n\nЕще не прошли наборов: {len(failures)-2}.'
    return CheckResult(number,success,passed,len(SCHEMAS),message)

def check_file(number,path=None):
    path=Path(path) if path else ROOT/f'answers/{int(number):02}.sql'
    return check(number,path.read_text())

def progress():
    try: state=json.loads((ROOT/'progress.json').read_text())
    except FileNotFoundError: state={}
    solved=[int(k) for k,v in state.items() if v['passed']]
    print(f'Решено: {len(solved)}/50')
    print('Готово: '+(', '.join(f'{n:02}' for n in sorted(solved)) or 'пока нет'))
    print('Остались: '+', '.join(f'{n:02}' for n in range(1,51) if n not in solved))

class Table:
    def __init__(self,result): self.columns,self.rows=result
    def __repr__(self): return str(self.columns)+'\n'+'\n'.join(map(str,self.rows[:40]))+f'\nВсего строк: {len(self.rows)}'
    def _repr_html_(self):
        head=''.join('<th style="text-align:left;padding:6px">'+escape(c)+'</th>' for c in self.columns)
        body=''.join('<tr>'+''.join('<td style="padding:6px;border-top:1px solid #ddd">'+escape('NULL' if v is None else str(v))+'</td>' for v in row)+'</tr>' for row in self.rows[:100])
        return f'<div style="overflow:auto"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div><p>{len(self.rows)} строк; показано до 100.</p>'

def sql(query_text,schema='public'): return Table(query(query_text,schema))

def status():
    try:
        print('PostgreSQL подключен:',query('SELECT version()')[1][0][0].split(' on ')[0])
        print('Данные подготовлены:',(ROOT/'data/seed-date.txt').read_text().strip())
        print('Доступны %%sql, %%check N, %task N, %hint N, %solution N и progress().')
    except (DatabaseError,FileNotFoundError) as exc: print(str(exc))

def install():
    from IPython import get_ipython
    from IPython.display import display
    ip=get_ipython()
    if ip is None: raise RuntimeError('install() вызывается в Jupyter/IPython. В терминале: python -m trainer ...')
    def check_magic(line,cell):
        try: display(check(int(line.strip()),cell))
        except (ValueError,OSError) as exc: print(str(exc))
    def sql_magic(line,cell):
        try: display(sql(cell,line.strip() or 'public'))
        except (ValueError,DatabaseError) as exc: print(str(exc))
    ip.register_magic_function(check_magic,'cell','check')
    ip.register_magic_function(sql_magic,'cell','sql')
    ip.register_magic_function(lambda line: show_task(int(line)),'line','task')
    ip.register_magic_function(lambda line: hint(int(line)),'line','hint')
    ip.register_magic_function(lambda line: solution(int(line)),'line','solution')
    status()

__all__=['install','check','check_file','sql','show_task','hint','solution','progress','status']
