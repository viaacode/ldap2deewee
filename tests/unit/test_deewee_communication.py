#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import uuid
from unittest.mock import patch
import json
from dataclasses import dataclass, field
from datetime import datetime

from viaa.configuration import ConfigParser

from deewee_communication import (
    PostgresqlWrapper, DeeweeClient,
    COUNT_ENTITIES_SQL, UPSERT_ENTITIES_SQL, MAX_LAST_MODIFIED_TIMESTAMP_SQL
)


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
        postgresql_wrapper.execute(UPSERT_ENTITIES_SQL, [key])
        cursor = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        assert cursor.execute.call_count == 1
        assert cursor.execute.call_args[0][0] == UPSERT_ENTITIES_SQL
        assert cursor.execute.call_args[0][1] == [key]

    @patch('psycopg2.connect')
    def test_executemany(self, mock_connect, postgresql_wrapper):
        values = [(str(uuid.uuid4()),), (str(uuid.uuid4()),)]
        postgresql_wrapper.executemany(UPSERT_ENTITIES_SQL, values)
        cursor = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        assert cursor.executemany.call_count == 1
        assert cursor.executemany.call_args[0][0] == UPSERT_ENTITIES_SQL
        assert cursor.executemany.call_args[0][1] == values


@dataclass
class ModifyTimestampMock:
    """Mock class of the returned modifyTimestamp by LDAP server"""

    value: datetime = datetime.now()


@dataclass
class LdapEntryMock:
    '''Mock class of LDAP3 Entry of ldap3 library'''

    entryUUID: uuid.UUID = uuid.uuid4()
    modifyTimestamp: ModifyTimestampMock = ModifyTimestampMock()
    atttributes: dict = field(default_factory=dict)

    def entry_to_json(self) -> str:
        return json.dumps(self.atttributes)


class TestDeeweeClient:

    @pytest.fixture
    @patch('deewee_communication.PostgresqlWrapper')
    def deewee_client(self, postgresql_wrapper_mock):
        return DeeweeClient({})

    def test_prepare_vars_upsert(self, deewee_client):
        ldap_result = LdapEntryMock()
        ldap_result.atttributes['dn'] = 'dn'
        value = deewee_client._prepare_vars_upsert(ldap_result, 'org')
        assert value == (str(ldap_result.entryUUID), 'org', ldap_result.entry_to_json(),
                         ldap_result.modifyTimestamp.value)

    def test_upsert_ldap_results_many(self, deewee_client):
        postgresql_wrapper_mock = deewee_client.postgresql_wrapper

        # Create 2 Mock LDAP results
        ldap_result_1 = LdapEntryMock()
        ldap_result_1.atttributes['dn'] = 'dn1'
        ldap_result_2 = LdapEntryMock()
        ldap_result_2.atttributes['dn'] = 'dn2'
        # Prepare to pass
        ldap_results = [([ldap_result_1], 'org'), ([ldap_result_2], 'person')]
        deewee_client.upsert_ldap_results_many(ldap_results)

        # The transformed mock LDAP result as tuple
        val1 = deewee_client._prepare_vars_upsert(ldap_result_1, 'org')
        val2 = deewee_client._prepare_vars_upsert(ldap_result_2, 'person')

        assert postgresql_wrapper_mock.executemany.call_count == 1
        assert postgresql_wrapper_mock.executemany.call_args[0][0] == UPSERT_ENTITIES_SQL
        assert postgresql_wrapper_mock.executemany.call_args[0][1] == [val1, val2]

    def test_max_last_modified_timestamp(self, deewee_client):
        postgresql_wrapper_mock = deewee_client.postgresql_wrapper
        dt = datetime.now()
        postgresql_wrapper_mock.execute.return_value = [[dt]]
        value = deewee_client.max_last_modified_timestamp()
        assert postgresql_wrapper_mock.execute.call_args[0][0] == MAX_LAST_MODIFIED_TIMESTAMP_SQL
        assert value == dt

    def test_count(self, deewee_client):
        postgresql_wrapper_mock = deewee_client.postgresql_wrapper
        postgresql_wrapper_mock.execute.return_value = [[5]]
        value = deewee_client.count()
        assert postgresql_wrapper_mock.execute.call_args[0][0] == COUNT_ENTITIES_SQL
        assert value == 5
