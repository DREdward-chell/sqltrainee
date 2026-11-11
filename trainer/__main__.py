import argparse
from . import check_file,show_task,hint,solution,progress,status
p=argparse.ArgumentParser(description='PostgreSQL тренажёр: 50 задач')
p.add_argument('command',choices=['check','task','hint','solution','progress','status'])
p.add_argument('number',type=int,nargs='?')
p.add_argument('file',nargs='?')
a=p.parse_args()
if a.command in ('progress','status'): globals()[a.command]()
else:
    if a.number is None: p.error('Нужен номер задачи 1..50')
    if a.command=='check':
        result=check_file(a.number,a.file); print(result); raise SystemExit(0 if result else 1)
    else: {'task':show_task,'hint':hint,'solution':solution}[a.command](a.number)
