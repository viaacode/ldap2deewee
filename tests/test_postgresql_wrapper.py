import pytest
import psycopg2
import uuid

from viaa.configuration import ConfigParser

from deewee_communication import PostgresqlWrapper


TABLE_NAME = 'entities'
COUNT_ENTITIES_SQL = f'SELECT COUNT(*) FROM {TABLE_NAME};'
SELECT_ENTITIES_SQL = f'SELECT * FROM {TABLE_NAME};'
INSERT_ENTITIES_SQL = f'INSERT INTO {TABLE_NAME} (ldap_uuid) VALUES (%s);'


@pytest.fixture
def postgresql_wrapper():
    """Returns a PostgresqlWrapper initiliazed by the parameters in config.yml"""
    return PostgresqlWrapper(ConfigParser().config['postgresql'])


@pytest.fixture
def postgresql_wrapper_invalid_credentials():
    """Returns a PostgresqlWrapper with invalid credentials"""
    params = ConfigParser().config['postgresql']
    params['password'] = 'wrong_pass'
    return PostgresqlWrapper(params)


def test_execute(postgresql_wrapper):
    assert postgresql_wrapper.execute(COUNT_ENTITIES_SQL) is not None


def test_execute_insert(postgresql_wrapper):
    count_before = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)[0][0]
    assert postgresql_wrapper.execute(INSERT_ENTITIES_SQL, [str(uuid.uuid4())]) is None
    count_after = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)[0][0]
    assert count_after == count_before + 1


def test_executemany(postgresql_wrapper):
    values = [(str(uuid.uuid4()),), (str(uuid.uuid4()),)]
    count_before = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)[0][0]
    postgresql_wrapper.executemany(INSERT_ENTITIES_SQL, values)
    count_after = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)[0][0]
    assert count_after == count_before + 2


def test_invalid_credentials(postgresql_wrapper_invalid_credentials):
    with pytest.raises(psycopg2.OperationalError):
        postgresql_wrapper_invalid_credentials.execute(COUNT_ENTITIES_SQL)
