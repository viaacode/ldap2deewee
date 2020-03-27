#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import patch
from datetime import datetime
from ldap3.core.exceptions import LDAPExceptionError
from psycopg2 import OperationalError as PSQLError

from app.app import App
from app.comm.deewee import DeeweeClient
from app.comm.ldap import LdapClient


class TestApp:

    @patch.object(App, '_sync', return_value=None)
    @patch.object(
        DeeweeClient, 'max_last_modified_timestamp', return_value=None
    )
    def test_main_full(self, max_last_modified_timestamp_mock, sync_mock):
        app = App()
        app.main()

        assert sync_mock.call_count == 1
        assert max_last_modified_timestamp_mock.call_count == 1

        call_arg = sync_mock.call_args[0][0]
        assert call_arg is None

    @patch.object(App, '_sync', return_value=None)
    @patch.object(
        DeeweeClient, 'max_last_modified_timestamp', return_value=datetime.now()
    )
    def test_main_diff(self, max_last_modified_timestamp_mock, sync_mock):
        app = App()
        app.main()

        assert sync_mock.call_count == 1
        assert max_last_modified_timestamp_mock.call_count == 1

        call_arg = sync_mock.call_args[0][0]
        assert type(call_arg) == datetime

    @patch.object(LdapClient, 'search_orgs', return_value=['org1'])
    @patch.object(LdapClient, 'search_people', return_value=['person1'])
    @patch.object(DeeweeClient, 'upsert_ldap_results_many', return_value=None)
    def test_sync(self, upsert_ldap_results_many_mock, search_people_mock, search_orgs_mock):
        app = App()
        app._sync()

        assert search_orgs_mock.call_count == 1
        assert search_people_mock.call_count == 1
        assert upsert_ldap_results_many_mock.call_count == 1

        assert search_orgs_mock.call_args[0][0] is None
        assert search_people_mock.call_args[0][0] is None
        assert upsert_ldap_results_many_mock.call_args[0][0] == [
            (['org1'], 'org'),
            (['person1'], 'person')
        ]

    @patch.object(DeeweeClient, 'max_last_modified_timestamp', side_effect=PSQLError)
    def test_main_psql_error(self, should_do_full_sync_mock):
        app = App()
        with pytest.raises(PSQLError):
            app.main()

    @patch.object(App, '_sync', side_effect=LDAPExceptionError)
    @patch.object(DeeweeClient, 'max_last_modified_timestamp', return_value=None)
    def test_main_ldap_error(self, should_do_full_sync_mock, sync_mock):
        app = App()
        with pytest.raises(LDAPExceptionError):
            app.main()
