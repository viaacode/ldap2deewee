import psycopg2


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
