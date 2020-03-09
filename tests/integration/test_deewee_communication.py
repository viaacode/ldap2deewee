import pytest
import psycopg2
import uuid
from datetime import datetime
from ldap3 import Server, Connection, MOCK_SYNC, ALL_ATTRIBUTES, OFFLINE_SLAPD_2_4
from testing.postgresql import PostgresqlFactory
import os

from deewee_communication import PostgresqlWrapper, DeeweeClient


TABLE_NAME = 'entities'
EXECUTE_SQL = f'SELECT version();'
COUNT_ENTITIES_SQL = f'SELECT COUNT(*) FROM {TABLE_NAME};'
INSERT_ENTITIES_SQL = f'INSERT INTO {TABLE_NAME} (ldap_uuid) VALUES (%s);'


# create initial data on create as fixtures into the database
def handler(postgresql):
    with open(f'{os.getcwd()}/additional_containers/postgresql/init.sql') as file:
        init_sql = file.read()
    conn = psycopg2.connect(**postgresql.dsn())
    cursor = conn.cursor()
    cursor.execute(init_sql)
    cursor.close()
    conn.commit()
    conn.close()


# Generate Postgresql class which shares the generated database
Postgresql = PostgresqlFactory(cache_initialized_db=True, on_initialized=handler)


def teardown_module(module):
    # clear cached database at end of tests
    Postgresql.clear_cache()


class TestPostgresqlWrapper:

    @classmethod
    def setup_class(cls):
        cls.postgresql = Postgresql()

    @classmethod
    def teardown_class(cls):
        cls.postgresql.stop()

    @pytest.fixture
    def postgresql_wrapper(self):
        """Returns a PostgresqlWrapper initiliazed by the parameters in config.yml"""
        return PostgresqlWrapper(self.postgresql.dsn())

    @pytest.fixture
    def postgresql_wrapper_invalid_credentials(self):
        """Returns a PostgresqlWrapper with invalid credentials"""
        params = self.postgresql.dsn()
        params['user'] = 'wrong_user'
        return PostgresqlWrapper(params)

    def test_execute(self, postgresql_wrapper):
        assert postgresql_wrapper.execute(EXECUTE_SQL) is not None

    def test_executemany(self, postgresql_wrapper):
        values = [(str(uuid.uuid4()),), (str(uuid.uuid4()),)]
        count_before = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)[0][0]
        postgresql_wrapper.executemany(INSERT_ENTITIES_SQL, values)
        count_after = postgresql_wrapper.execute(COUNT_ENTITIES_SQL)[0][0]
        assert count_after == count_before + 2

    def test_invalid_credentials(self, postgresql_wrapper_invalid_credentials):
        with pytest.raises(psycopg2.OperationalError):
            postgresql_wrapper_invalid_credentials.execute(EXECUTE_SQL)


class TestDeeweeClient:

    @classmethod
    def setup_class(cls):
        cls.postgresql = Postgresql()

    @classmethod
    def teardown_class(cls):
        cls.postgresql.stop()

    @pytest.fixture
    def deewee_client(self):
        """Returns a DeeweeClient initiliazed linked to the temporary test DB

        Also truncates the target table.
        """
        deewee_client = DeeweeClient(self.postgresql.dsn())
        deewee_client.truncate_table()
        return deewee_client

    def _mock_orgs_people(self):
        """Creates and returns some LDAP entries via ldap3 mock functionality"""
        # Create mock server with openLDAP schema
        server = Server('mock_server', get_info=OFFLINE_SLAPD_2_4)
        conn = Connection(server, 'uid=admin,dc=hetarchief,dc=be', 'Secret123', client_strategy=MOCK_SYNC)
        conn.strategy.add_entry('uid=admin,dc=hetarchief,dc=be', {'userPassword': 'Secret123', 'sn': 'admin_sn'})

        now = datetime.now()
        conn.bind()
        # Create orgs OU
        conn.add('ou=orgs,dc=hetarchief,dc=be', 'organizationalUnit')
        # Create 2 orgs
        conn.add('o=1,ou=orgs,dc=hetarchief,dc=be', 'organization',
                 {'o': '1', 'entryuuid': str(uuid.uuid4()), 'modifyTimestamp': now,
                  'sn': 'test1', 'telephoneNumber': 1111})
        conn.add('o=2,ou=orgs,dc=hetarchief,dc=be', 'organization',
                 {'o': '2', 'entryuuid': str(uuid.uuid4()), 'modifyTimestamp': now,
                  'sn': 'test2', 'telephoneNumber': 1112})

        # Create people OU
        conn.add('ou=people,dc=hetarchief,dc=be', 'organizationalUnit')
        # create 2 people
        conn.add('mail=test1@test.test,ou=people,dc=hetarchief,dc=be', 'inetOrgPerson',
                 {'mail': 'test1@test.test', 'entryuuid': str(uuid.uuid4()),
                  'modifyTimestamp': now, 'sn': 'test1', 'telephoneNumber': 1111})
        conn.add('mail=test2@test.test,ou=people,dc=hetarchief,dc=be', 'inetOrgPerson',
                 {'mail': 'test2@test.test', 'entryuuid': str(uuid.uuid4()),
                  'modifyTimestamp': now, 'sn': 'test2', 'telephoneNumber': 1112})

        attrs = [ALL_ATTRIBUTES, 'modifyTimestamp', 'entryUUID']
        conn.search('ou=orgs,dc=hetarchief,dc=be', '(&(objectClass=*)(!(ou=orgs)))', attributes=attrs)
        orgs = conn.entries

        conn.search('ou=people,dc=hetarchief,dc=be', '(&(objectClass=*)(!(ou=people)))', attributes=attrs)
        people = conn.entries
        return (orgs, people)

    def test_max_last_modified_timestamp(self, deewee_client):
        now = datetime.now()
        assert deewee_client.max_last_modified_timestamp() is None
        deewee_client.insert_entity(now)
        assert deewee_client.max_last_modified_timestamp() == now

    def test_upsert_ldap_results_many(self, deewee_client):
        orgs, people = self._mock_orgs_people()
        assert deewee_client.count() == 0
        deewee_client.upsert_ldap_results_many([(orgs, 'org'), (people, 'person')])
        assert deewee_client.count_type('org') == 2
        assert deewee_client.count_type('person') == 2

    def insert_count(self, deewee_client):
        assert deewee_client.count() == 0
        deewee_client.insert_entity()
        assert deewee_client.count() == 1
