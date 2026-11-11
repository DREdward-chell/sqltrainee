from pathlib import Path
from html import escape
import base64
import json
from notebook_format import format_cell, format_markdown, cell_metadata
ROOT=Path(__file__).resolve().parents[1]
T=json.loads((ROOT/'trainer/tasks.json').read_text())
# Статическая инженерная схема, встроенная в notebook для автономного просмотра.
parts=['''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1220" viewBox="0 0 1080 1220">
<rect width="1080" height="1220" fill="#f4f7fb"/>
<style>text{font-family:Arial,sans-serif;fill:#17243a} .name{font-size:21px;font-weight:bold}.field{font-family:monospace;font-size:15px}.label{font-size:14px;fill:#275d91}.line{fill:none;stroke:#5e82a7;stroke-width:2}</style>
<text x="50" y="45" font-size="26" font-weight="bold">Фриланс-биржа · схема PostgreSQL</text>
<text x="50" y="74" font-size="15">PK — первичный ключ, FK — внешний ключ · значения 0..N и 0..1 обозначают кратность</text>''']
def box(x,y,w,title,fields):
    h=62+25*len(fields)
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="white" stroke="#c4d3e2"/>')
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="44" rx="10" fill="#e0edfa"/>')
    parts.append(f'<text class="name" x="{x+16}" y="{y+29}">{title}</text>')
    for i,f in enumerate(fields): parts.append(f'<text class="field" x="{x+16}" y="{y+68+i*25}">{escape(f)}</text>')
def line(path,x,y,label):
    parts.append(f'<path class="line" d="{path}"/><text class="label" x="{x}" y="{y}">{escape(label)}</text>')
box(330,110,420,'users',['id PK · bigint','name · text','registered_at · timestamp'])
box(50,335,400,'customers',['user_id PK, FK → users.id'])
box(620,335,410,'freelancers',['user_id PK, FK → users.id','specialization · text','hourly_rate · numeric(12,2)'])
box(50,575,440,'projects',['id PK · bigint','customer_id FK → customers.user_id','title, description · text','budget · numeric(14,2)','status · text','created_at · timestamp','completed_at · timestamp / NULL'])
box(620,575,410,'bids',['id PK · bigint','project_id FK → projects.id','freelancer_id FK → freelancers.user_id','amount · numeric(14,2)','proposed_completion_date · date','status · text','submitted_at · timestamp','accepted_at · timestamp / NULL','rejected_at · timestamp / NULL'])
box(50,940,440,'reviews',['project_id PK, FK → projects.id','rating · smallint [1..5]','comment · text','created_at · timestamp'])
line('M 400 247 V 288 H 250 V 335',72,279,'users 1 → customers 0..1')
line('M 680 247 V 288 H 825 V 335',712,279,'users 1 → freelancers 0..1')
line('M 250 422 V 575',65,510,'customers 1 → projects 0..N')
line('M 825 472 V 575',646,528,'freelancers 1 → bids 0..N')
line('M 490 700 H 620',501,673,'1 → 0..N')
line('M 250 812 V 940',63,900,'projects 1 → reviews 0..1')
parts.append('<text x="620" y="965" font-size="16" font-weight="bold">Ограничения заявок</text>')
for i,s in enumerate(['UNIQUE(project_id, freelancer_id)','≤ 1 принятой заявки на проект','Суммы и ставки строго > 0','Отзыв — только после завершения','Автор и получатель отзыва','определяются через проект и заявку.']):
    parts.append(f'<text x="620" y="{995+i*26}" font-size="15">{escape(s)}</text>')
parts.append('</svg>')
svg=''.join(parts)
(ROOT/'models/schema.svg').write_text(svg)

def md(s): return {'cell_type':'markdown','metadata':{},'source':s.splitlines(True)}
def code(s): return {'cell_type':'code','metadata':{},'source':s.splitlines(True),'execution_count':None,'outputs':[]}
def notebook(cells,path):
    for i,c in enumerate(cells):
        c['id']=f'cell-{i:03}'
        source=''.join(c['source'])
        if c['cell_type']=='code': c['metadata'].update(cell_metadata(source))
        c['source']=(format_cell(source) if c['cell_type']=='code' else format_markdown(source)).splitlines(True)
    obj={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3 (ipykernel)','language':'python','name':'python3'},'language_info':{'name':'python','file_extension':'.py','mimetype':'text/x-python','pygments_lexer':'ipython3'}},'nbformat':4,'nbformat_minor':5}
    (ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n')

cells=[md('''# PostgreSQL · 50 задач перед контрольной

**Пиши → запускай Shift+Enter → исправляй → проверяй снова.**

Задачи **1–6** повторяют запросы **3–8** из твоего примера. Затем сложность растет до окон, множеств и серий дат.

1. Запусти ячейку подключения ниже. В Docker база запускается автоматически вместе с контейнером.
2. В ячейке `%%check N` замени комментарий своим SQL. Первая строка должна остаться.
3. Для исследования данных используй `%%sql`. Подсказка: `%hint N`; эталон: `%solution N`; прогресс: `progress()`.

Ответы сохраняются в `answers/NN.sql`. Проверка сравнивает результаты на 5 наборах, включая пустой. **Таблицы пиши без `public.`**. Колонки — точно как в условии. Если сортировка не указана, порядок строк не важен, но дубликаты важны. Числа сравниваются после округления до 6 знаков.

**Моделирование М1/М2:** отдельные задания и чек-лист в `models/README.md`. **Пробная контрольная:** `exam.ipynb`.'''),
code('from trainer import *\ninstall()'),
md('''## Осмотр данных

Входная роль — только чтение; запрос не испортит учебные таблицы. Предел одного запроса — 4 секунды. `%%sql check_1` переключает предварительный просмотр на альтернативный набор.'''),
code('%%sql\nSELECT id, title, budget, status, completed_at\nFROM projects\nORDER BY id\nLIMIT 10;')]
diagram=md('## Карта базы\n\n![ER-диаграмма](attachment:schema.svg)')
diagram['attachments']={'schema.svg':{'image/svg+xml':base64.b64encode(svg.encode()).decode()}}
cells.append(diagram)
cells.append(md('''### Словарь колонок

| Таблица | Колонки |
|---|---|
| `users` | `id`, `name`, `registered_at` |
| `customers` | `user_id` (PK и FK → users.id) |
| `freelancers` | `user_id` (PK и FK), `specialization`, `hourly_rate` |
| `projects` | `id`, `customer_id`, `title`, `description`, `budget`, `status`, `created_at`, `completed_at` |
| `bids` | `id`, `project_id`, `freelancer_id`, `amount`, `proposed_completion_date`, `status`, `submitted_at`, `accepted_at`, `rejected_at` |
| `reviews` | `project_id` (PK и FK), `rating`, `comment`, `created_at` |

Проекты: **открыт / в работе / завершен**. Заявки: **подана / принята / отклонена**. Исполнитель — фрилансер принятой заявки. Одна заявка человека на проект; максимум один победитель; один отзыв на завершенный проект.

Даты событий — timestamp, обещанный день — date, деньги — numeric. Часовая ставка (`hourly_rate`), бюджет проекта (`budget`) и предложенная цена (`amount`) — разные величины. Имена пользователей могут повторяться.

В спорных формулировках приняты явные правила: непустые проекты в №2; все проекты в знаменателе №3; 10% от меньшей суммы в №6. На контрольной эти трактовки лучше обозначить в ответе.'''))
sections={1:'I · Запросы из примера контрольной',7:'II · JOIN, группировки и исключения',19:'III · Окна, ранги и даты',31:'IV · Множества и сложные условия',41:'V · Продвинутые отчеты'}
for t in T:
    n=t['id']
    if n in sections: cells.append(md('## '+sections[n]))
    cells.append(md(f"### {n:02}. {t['title']}\n\nСложность **{t['level']}/5**.\n\n{t['text']}\n\n**Колонки в указанном порядке:** "+', '.join('`'+c+'`' for c in t['columns'])+'.\n\n'+('**Порядок строк проверяется.**' if t['ordered'] else 'Порядок строк не важен.')+f' Подсказка по запросу: `%hint {n}`.'))
    cells.append(code(f'%%check {n}\n-- Напиши один SELECT или WITH ... SELECT.\n'))
cells.extend([md('## Прогресс\n\nСохраняется результат последней проверки каждой задачи. Эталоны можно открыть через `%solution N` после самостоятельной попытки.'),code('progress()')])
notebook(cells,'training.ipynb')
exam=[md('''# Пробная контрольная · 90 минут

**8 заданий, 10 баллов.** М1 и М2 по 1 баллу, запросы 3–6 по 1, запросы 7–8 по 2. Условия запросов ниже соответствуют первым шести задачам тренажера с явно оговоренными спорными трактовками.

Сначала моделирование, затем запросы. Открой ноутбук заново для новой попытки. `%%answer N` только запоминает текст: автопроверка находится **в самом конце**. Не используй Run All до окончания работы.

Область: заказчики публикуют проекты; фрилансеры с именем, датой регистрации, специализацией и ставкой отправляют заявки с ценой и обещанной датой завершения. При выборе заявки проект переходит в работу, остальные заявки отклоняются. Даты подачи и решений хранятся. После завершения заказчик оставляет один отзыв с рейтингом 1..5. Допускаются пользователи с обеими ролями.

Для заданий 3–8 используй схему тренажера. М1/М2 оценивай по `models/README.md`, когда закончишь.'''),code('''import time
from IPython import get_ipython
from IPython.display import display
from trainer import check
started_at = time.monotonic()
exam_answers = {}
def remember_answer(line, cell):
    number = int(line.strip())
    if not 2 <= number <= 8:
        raise ValueError("Номер задания: 2..8")
    exam_answers[number] = cell
    print(f"Ответ {number} сохранен в памяти. Проверка — в конце notebook.")
get_ipython().register_magic_function(remember_answer, "cell", "answer")
print("Таймер начался. 90 минут.")'''),
md('## 1. Концептуальная модель · 1 балл · 10 минут\n\nНарисуй ER/UML-диаграмму. Все сущности, ключевые атрибуты, связи и кардинальности. Диаграмму можно вставить сюда или сохранить рядом.'),
md('*Место для своей диаграммы и пояснений.*'),
md('## 2. Логическая модель · 1 балл · 15 минут\n\nНапиши CREATE TABLE со всеми PK/FK, NOT NULL, UNIQUE и CHECK. Объясни, какие правила требуют триггера/транзакции.'),
code('%%answer 2\n-- Твои CREATE TABLE. Эта ячейка не изменяет учебную базу.')]
for i,t in enumerate(T[:6],3):
    exam.append(md(f"## {i}. {t['title']} · {2 if i>=7 else 1} балл\n\n{t['text']}\n\nКолонки: "+', '.join('`'+c+'`' for c in t['columns'])+'.'))
    exam.append(code(f'%%answer {i}\n-- Твой запрос.'))
exam.extend([md('## Стоп: проверка после завершения\n\nЗапусти следующую ячейку, когда сдашь работу самому себе. Максимум за SQL: 8 баллов; еще 2 балла за моделирование оцени вручную по чек-листу.'),
code('''print(f"Прошло {(time.monotonic() - started_at)/60:.1f} минут")
points = 0
for number in range(3, 9):
    result = check(number - 2, exam_answers.get(number, ""), save=False)
    display(result)
    if result.passed:
        points += 2 if number >= 7 else 1
print(f"SQL: {points}/8. Моделирование: до 2 баллов по чек-листу.")''')])
notebook(exam,'exam.ipynb')
print('Notebooks and SVG written')
