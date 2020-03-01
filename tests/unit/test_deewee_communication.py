import pytest
import uuid
from unittest.mock import patch

from viaa.configuration import ConfigParser

from deewee_communication import PostgresqlWrapper

TABLE_NAME = 'entities'
COUNT_ENTITIES_SQL = f'SELECT COUNT(*) FROM {TABLE_NAME};'
INSERT_ENTITIES_SQL = f'INSERT INTO {TABLE_NAME} (ldap_uuid) VALUES (%s);'


class TestPostgresqlWrapper:

    @pytest.fixture
    def postgresql_wrapper(self):
        """Returns a PostgresqlWrapper initiliazed by the parameters in config.yml"""
        return PostgresqlWrapper(ConfigParser().config['postgresql'])

    @patch('psycopg2.connect')
    def test_execute(self, mock_connect, postgresql_wrapper):
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = 5
        result = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)
        assert result == 5

    @patch('psycopg2.connect')
    def test_execute_insert(self, mock_connect, postgresql_wrapper):
        key = str(uuid.uuid4())
        mock_connect.cursor.return_value.description = None
        postgresql_wrapper.execute(INSERT_ENTITIES_SQL, [key])
        cursor = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        assert cursor.execute.call_count == 1
        assert cursor.execute.call_args[0][0] == INSERT_ENTITIES_SQL
        assert cursor.execute.call_args[0][1] == [key]

    @patch('psycopg2.connect')
    def test_executemany(self, mock_connect, postgresql_wrapper):
        values = [(str(uuid.uuid4()),), (str(uuid.uuid4()),)]
        postgresql_wrapper.executemany(INSERT_ENTITIES_SQL, values)
        cursor = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        assert cursor.executemany.call_count == 1
        assert cursor.executemany.call_args[0][0] == INSERT_ENTITIES_SQL
        assert cursor.executemany.call_args[0][1] == values
