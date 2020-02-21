import psycopg2
from datetime import datetime


class PostgresqlWrapper:
    """Allows for executing SQL statements to a postgresql database"""
    def __init__(self, params: dict):
        self.params_postgresql = params

    def execute(self, query: str, vars=None):
        """Connects to the postgresql DB and executes the statement.

        Returns all results of the statement if applicable.
        """
        with psycopg2.connect(**self.params_postgresql) as conn:
            with conn.cursor() as curs:
                curs.execute(query, vars)
                if curs.description is not None:
                    return curs.fetchall()

    def executemany(self, query: str, vars_list: list):
        """Connects to the postgresql DB and executes the many statement"""
        with psycopg2.connect(**self.params_postgresql) as conn:
            with conn.cursor() as curs:
                curs.executemany(query, vars_list)


class DeeweeClient:
    """Acts as a client to query and modify information from and to DEEWEE"""

    TABLE_NAME = 'entities'
    INSERT_ENTITIES_SQL = f'INSERT INTO {TABLE_NAME} \
                            (ldap_uuid, type, content, last_modified_timestamp) \
                            VALUES (%s, %s, %s, %s);'
    UPDATE_ENTITIES_SQL = f'UPDATE {TABLE_NAME} SET content = %s, \
                            last_modified_timestamp = %s WHERE ldap_UUID = %s;'
    TRUNCATE_ENTITIES_SQL = f'TRUNCATE TABLE {TABLE_NAME};'
    COUNT_ENTITIES_SQL = f'SELECT COUNT(*) FROM {TABLE_NAME}'
    COUNT_ENTITIES_TYPE_SQL = f'{COUNT_ENTITIES_SQL} where type = %s;'
    MAX_LAST_MODIFIED_TIMESTAMP_SQL = f'SELECT max(last_modified_timestamp) FROM {TABLE_NAME};'

    def __init__(self, params: dict):
        self.postgresql_wrapper = PostgresqlWrapper(params)

    def _prepare_vars_insert(self, ldap_result, type: str) -> tuple:
        """Transforms an LDAP entry to pass to the psycopg2 execute function.

        Transform it to a tuple containing the parameters to insert in a new row.
        """

        return (str(ldap_result.entryUUID), type, ldap_result.entry_to_json(),
                ldap_result.modifyTimestamp.value)

    def _prepare_vars_update(self, ldap_result) -> tuple:
        """Transforms an LDAP entry to pass to the psycopg2 execute function.

        Transform it to a tuple containing the parameters to update an existing row.
        """
        return (ldap_result.entry_to_json(), ldap_result.modifyTimestamp.value,
                str(ldap_result.entryUUID))

    def insert_ldap_results_many(self, ldap_results: list, type):
        # Parse the SQL values from the ldap results as a passable list
        vars_list = [self._prepare_vars_insert(ldap_result, type) for ldap_result in ldap_results]
        self.postgresql_wrapper.executemany(self.INSERT_ENTITIES_SQL, vars_list)

    def insert_ldap_results(self, ldap_results: list, type):
        for ldap_result in ldap_results:
            vars = self._prepare_vars_insert(ldap_result, type)
            self.postgresql_wrapper.execute(self.INSERT_ENTITIES_SQL, vars)

    def update_ldap_results(self, ldap_results: list):
        for ldap_result in ldap_results:
            vars = self._prepare_vars_update(ldap_result)
            self.postgresql_wrapper.execute(self.UPDATE_ENTITIES_SQL, vars)

    def max_last_modified_timestamp(self) -> datetime:
        """Returns the highest last_modified_timestamp"""
        return self.postgresql_wrapper.execute(self.MAX_LAST_MODIFIED_TIMESTAMP_SQL)[0][0]

    def exists(self, ldap_UUID: str) -> bool:
        return self.count_where('ldap_uuid = %s', (ldap_UUID,)) == 1

    def insert_entity(self, date_time: datetime = datetime.now()):
        vars = ('550e8400-e29b-41d4-a716-446655440000', 'person', '{"key": "value"}', date_time)
        self.postgresql_wrapper.execute(self.INSERT_ENTITIES_SQL, vars)

    def count(self) -> int:
        return self.postgresql_wrapper.execute(self.COUNT_ENTITIES_SQL)[0][0]

    def count_where(self, where_clausule: str, vars: tuple = None) -> int:
        """Constructs and executes a 'select count(*) where' statement.

        The where clausule can contain zero or more paremeters.

        If there are no parameters e.g. where_clausule = "column is null", vars should be None.
        If there are one or more parameters e.g. where_clausule = "column = %s",
            vars should be a tuple containing the parameters.

        Arguments:
            where_clausule -- represents the entire clausule that comes after the where keyword
            vars -- see above

        Returns:
            int -- the amount of records
        """
        select_sql = f'{self.COUNT_ENTITIES_SQL} where {where_clausule};'
        return self.postgresql_wrapper.execute(select_sql, vars)[0][0]

    def count_type(self, type: str) -> int:
        return self.count_where('type = %s', (type,))

    def truncate_table(self):
        self.postgresql_wrapper.execute(self.TRUNCATE_ENTITIES_SQL)
