#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from datetime import datetime
from functools import wraps


class PostgresqlWrapper:
    """Allows for executing SQL statements to a postgresql database"""
    def __init__(self, params: dict):
        self.params_postgresql = params

    def _connect_curs_postgresql(function):
        """Wrapper function that connects and authenticates to the PostgreSQL DB.

        The passed function will receive the open cursor.
        """
        @wraps(function)
        def wrapper_connect(self, *args, **kwargs):
            with psycopg2.connect(**self.params_postgresql) as conn:
                with conn.cursor() as curs:
                    val = function(self, cursor=curs, *args, **kwargs)
            return val
        return wrapper_connect

    @_connect_curs_postgresql
    def execute(self, query: str, vars=None, cursor=None):
        """Connects to the postgresql DB and executes the statement.

        Returns all results of the statement if applicable.
        """
        cursor.execute(query, vars)
        if cursor.description is not None:
            return cursor.fetchall()

    @_connect_curs_postgresql
    def executemany(self, query: str, vars_list: list, cursor=None):
        """Connects to the postgresql DB and executes the many statement"""
        cursor.executemany(query, vars_list)


class DeeweeClient:
    """Acts as a client to query and modify information from and to DEEWEE"""

    TABLE_NAME = 'entities'
    UPSERT_ENTITIES_SQL = f'INSERT INTO {TABLE_NAME} \
                            (ldap_uuid, type, content, last_modified_timestamp) \
                            VALUES (%s, %s, %s, %s) \
                            ON CONFLICT (ldap_uuid) DO UPDATE \
                                SET content = EXCLUDED.content, \
                                last_modified_timestamp = EXCLUDED.last_modified_timestamp'
    TRUNCATE_ENTITIES_SQL = f'TRUNCATE TABLE {TABLE_NAME};'
    COUNT_ENTITIES_SQL = f'SELECT COUNT(*) FROM {TABLE_NAME}'
    MAX_LAST_MODIFIED_TIMESTAMP_SQL = f'SELECT max(last_modified_timestamp) FROM {TABLE_NAME}'

    def __init__(self, params: dict):
        self.postgresql_wrapper = PostgresqlWrapper(params)

    def _prepare_vars_upsert(self, ldap_result, type: str) -> tuple:
        """Transforms an LDAP entry to pass to the psycopg2 execute function.

        Transform it to a tuple containing the parameters to be able to upsert.
        """
        return (str(ldap_result.entryUUID), type, ldap_result.entry_to_json(),
                ldap_result.modifyTimestamp.value)

    def upsert_ldap_results_many(self, ldap_results: list):
        """Upsert the LDAP entries into PostgreSQL.

       Transforms and flattens the LDAP entries to one list in order to execute in one transaction.

        Arguments:
            ldap_results -- list of two-tuples. The tuple contains a list of LDAP entries and a type (str)
        """
        vars_list = []
        for ldap_result_tuple in ldap_results:
            type = ldap_result_tuple[1]
            # Parse and flatten the SQL values from the ldap_results as a passable list
            vars_list.extend([self._prepare_vars_upsert(ldap_result, type) for ldap_result in ldap_result_tuple[0]])
        self.postgresql_wrapper.executemany(self.UPSERT_ENTITIES_SQL, vars_list)

    def max_last_modified_timestamp(self) -> datetime:
        """Returns the highest last_modified_timestamp"""
        return self.postgresql_wrapper.execute(self.MAX_LAST_MODIFIED_TIMESTAMP_SQL)[0][0]

    def insert_entity(self, date_time: datetime = datetime.now()):
        vars = ('550e8400-e29b-41d4-a716-446655440000', 'person', '{"key": "value"}', date_time)
        self.postgresql_wrapper.execute(self.UPSERT_ENTITIES_SQL, vars)

    def count(self) -> int:
        return self.postgresql_wrapper.execute(self.COUNT_ENTITIES_SQL)[0][0]

    def count_where(self, where_clause: str, vars: tuple = None) -> int:
        """Constructs and executes a 'select count(*) where' statement.

        The where clause can contain zero or more paremeters.

        If there are no parameters e.g. clause = "column is null", vars should be None.
        If there are one or more parameters e.g. where_clause = "column = %s",
            vars should be a tuple containing the parameters.

        Arguments:
            where_clause -- represents the entire clause that comes after the where keyword
            vars -- see above

        Returns:
            int -- the amount of records
        """
        select_sql = f'{self.COUNT_ENTITIES_SQL} where {where_clause};'
        return self.postgresql_wrapper.execute(select_sql, vars)[0][0]

    def count_type(self, type: str) -> int:
        return self.count_where('type = %s', (type,))

    def truncate_table(self):
        self.postgresql_wrapper.execute(self.TRUNCATE_ENTITIES_SQL)
