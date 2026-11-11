"""Минимальный драйвер libpq: настоящие запросы PostgreSQL, без pip-зависимостей."""
import ctypes as C
import ctypes.util
from decimal import Decimal
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get('SQLTRAINER_PORT', '55432'))
SCHEMAS = ('public', 'check_1', 'check_2', 'check_3', 'check_empty')

class DatabaseError(RuntimeError):
    pass

_lib = None

def library():
    global _lib
    if _lib is not None:
        return _lib
    candidates = [os.environ.get('SQLTRAINER_LIBPQ'), ctypes.util.find_library('pq'),
                  '/opt/homebrew/opt/postgresql@17/lib/libpq.dylib',
                  '/opt/homebrew/opt/libpq/lib/libpq.dylib']
    for path in filter(None, candidates):
        try:
            lib = C.CDLL(path)
            break
        except OSError:
            continue
    else:
        raise DatabaseError('Не найдена libpq. Установите PostgreSQL или задайте SQLTRAINER_LIBPQ.')
    signatures = {
        'PQconnectdb': (C.c_void_p, [C.c_char_p]), 'PQstatus': (C.c_int, [C.c_void_p]),
        'PQerrorMessage': (C.c_char_p, [C.c_void_p]), 'PQfinish': (None, [C.c_void_p]),
        'PQexecParams': (C.c_void_p, [C.c_void_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_int]),
        'PQresultStatus': (C.c_int,[C.c_void_p]), 'PQresultErrorMessage': (C.c_char_p,[C.c_void_p]),
        'PQntuples': (C.c_int,[C.c_void_p]), 'PQnfields': (C.c_int,[C.c_void_p]),
        'PQfname': (C.c_char_p,[C.c_void_p,C.c_int]), 'PQftype': (C.c_uint,[C.c_void_p,C.c_int]),
        'PQgetisnull': (C.c_int,[C.c_void_p,C.c_int,C.c_int]),
        'PQgetvalue': (C.c_char_p,[C.c_void_p,C.c_int,C.c_int]), 'PQclear': (None,[C.c_void_p])}
    for name,(restype,argtypes) in signatures.items():
        f=getattr(lib,name); f.restype=restype; f.argtypes=argtypes
    _lib=lib
    return lib

class Connection:
    def __init__(self, schema='public', admin=False):
        if schema not in SCHEMAS:
            raise ValueError('Неизвестный набор данных')
        self.lib=library()
        role='sqltrainer_admin' if admin else 'sqltrainee'
        # Quote libpq values, including passwords with spaces, quotes or backslashes.
        def quote(value):
            return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"
        options = {'host': os.environ.get('SQLTRAINER_HOST', '127.0.0.1'),
                   'port': PORT, 'dbname': os.environ.get('SQLTRAINER_DATABASE', 'sqltrainee'),
                   'user': role, 'connect_timeout': 3}
        password = os.environ.get('SQLTRAINER_ADMIN_PASSWORD' if admin else 'SQLTRAINER_PASSWORD')
        if password is not None:
            options['password'] = password
        self.conn=self.lib.PQconnectdb(' '.join(f'{k}={quote(v)}' for k,v in options.items()).encode())
        if not self.conn or self.lib.PQstatus(self.conn):
            msg=self.lib.PQerrorMessage(self.conn).decode() if self.conn else 'Out of memory'
            self.close()
            raise DatabaseError(msg+'\nЗапустите БД: docker start sqltrainee (фоновый Docker-контейнер) или bash scripts/start.sh (локальная установка)')
        self.execute(f'SET search_path TO {schema}, pg_catalog')
        self.execute("SET TIME ZONE 'Europe/Moscow'")
        self.execute("SET statement_timeout='4s'")
        self.execute("SET lock_timeout='1s'")
    def execute(self, sql):
        r=self.lib.PQexecParams(self.conn,sql.encode(),0,None,None,None,None,0)
        if not r:
            raise DatabaseError(self.lib.PQerrorMessage(self.conn).decode())
        try:
            status=self.lib.PQresultStatus(r)
            if status not in (1,2):
                raise DatabaseError(self.lib.PQresultErrorMessage(r).decode().strip())
            cols=[self.lib.PQfname(r,c).decode() for c in range(self.lib.PQnfields(r))]
            types=[self.lib.PQftype(r,c) for c in range(len(cols))]
            rows=[]
            for row in range(self.lib.PQntuples(r)):
                values=[]
                for col,oid in enumerate(types):
                    if self.lib.PQgetisnull(r,row,col): value=None
                    else:
                        value=self.lib.PQgetvalue(r,row,col).decode()
                        if oid in (20,21,23): value=int(value)
                        elif oid in (700,701,1700): value=Decimal(value)
                        elif oid==16: value=value=='t'
                    values.append(value)
                rows.append(tuple(values))
            return cols,rows
        finally:
            self.lib.PQclear(r)
    def close(self):
        if getattr(self,'conn',None): self.lib.PQfinish(self.conn); self.conn=None
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

def query(sql, schema='public'):
    with Connection(schema) as c:
        # Extended-query protocol rejects multiple statements, read-only transaction protects data.
        c.execute('BEGIN READ ONLY')
        try:
            result=c.execute(sql)
            if not result[0]: raise DatabaseError('Нужен один SELECT или WITH ... SELECT, возвращающий таблицу.')
            return result
        finally:
            c.execute('ROLLBACK')
