# app/database.py
import sqlite3
import os
from flask import g
from app.config import settings

try:
    import psycopg2
    import psycopg2.extras
    _HAS_PSYCOPG2 = True
except ImportError:
    _HAS_PSYCOPG2 = False

class DatabaseManager:
    def __init__(self, database_url):
        self.database_url = database_url
        self.connection = None
        self.db_type = 'sqlite'
        self.param_style = 'qmark' # Default for SQLite

        if self.database_url.startswith('postgresql'):
            if not _HAS_PSYCOPG2:
                # В продакшене это критическая ошибка, в тестах можно перехватить
                raise ImportError("psycopg2-binary is required for PostgreSQL connections but not found.")
            self.db_type = 'postgresql'
            self.param_style = 'pyformat' # %s for psycopg2
            self.connection_args = {
                "dsn": self.database_url,
                "cursor_factory": psycopg2.extras.RealDictCursor
            }
        elif self.database_url.startswith('sqlite'):
            self.db_type = 'sqlite'
            self.param_style = 'qmark' # ? for sqlite3
            self.connection_args = {
                "database": self.database_url.replace('sqlite:///', ''),
                "check_same_thread": False 
            }
            if ':memory:' in self.database_url or './test.db' in self.database_url:
                self.connection_args['uri'] = True
        else:
            raise ValueError(f"Unsupported database URL schema: {database_url}")

    def get_connection(self):
        if self.connection is None:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(**self.connection_args)
            elif self.db_type == 'sqlite':
                self.connection = sqlite3.connect(**self.connection_args)
                self.connection.row_factory = sqlite3.Row 
            
        return self.connection

    def close_connection(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetch_one(self, query, params=()):
        cursor = self.get_connection().cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=()):
        cursor = self.get_connection().cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
        
    def create_all_tables(self, schema_file='schema.sql'):
        conn = self.get_connection()
        with open(schema_file, 'r', encoding='utf-8') as f:
            script = f.read()
            if self.db_type == 'sqlite':
                conn.executescript(script)
            elif self.db_type == 'postgresql':
                cursor = conn.cursor()
                for statement in script.split(';'):
                    if statement.strip():
                        # PostgreSQL не поддерживает множественные statements в execute()
                        # А также нужно обрабатывать DROP TABLE IF EXISTS без CASCADE
                        try:
                            cursor.execute(statement)
                        except psycopg2.Error as e:
                            # 42P01 - undefined_table, если DROP IF EXISTS пытается удалить несуществующую таблицу
                            # 25P02 - in_failed_sql_transaction, если предыдущая ошибка привела к состоянию отката
                            # Если это ошибка, которую мы ожидаем (таблица не существует), то игнорируем
                            if e.pgcode == '42P01': # undefined_table
                                conn.rollback() # Откатываем транзакцию, если была ошибка, но хотим продолжить
                            else:
                                raise 
                conn.commit()
        conn.commit() # Важно для подтверждения изменений

    def recreate_tables(self, schema_file='schema.sql'):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table['name']
                if table_name.startswith('sqlite_'):
                    continue
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        elif self.db_type == 'postgresql':
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%' AND tablename NOT LIKE 'sql_%';
            """)
            tables = cursor.fetchall()
            for table in tables:
                table_name = table['tablename']
                cursor.execute(f"DROP TABLE IF EXISTS \"{table_name}\" CASCADE;") # С CASCADE для PostgreSQL
        
        conn.commit()
        self.create_all_tables(schema_file)

db_manager = DatabaseManager(settings.DATABASE_URL)