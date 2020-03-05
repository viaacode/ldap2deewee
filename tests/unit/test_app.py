import pytest
from unittest.mock import patch
from datetime import datetime
from ldap3.core.exceptions import LDAPExceptionError
from psycopg2 import OperationalError as PSQLError

from app import App
from deewee_communication import DeeweeClient
from ldap_communication import LdapClient


class TestApp:

    @patch.object(DeeweeClient, 'count', return_value=0)
    def test_should_do_full_sync(self, count_mock):
        """If the target table is empty, a full load is needed"""
        app = App()
        full_sync = app._should_do_full_sync()

        assert count_mock.call_count == 1
        assert full_sync

    @patch.object(DeeweeClient, 'count', return_value=1)
    def test_should_do_full_sync_not(self, count_mock):
        """If the target table is not empty, a full load is not needed"""
        app = App()
        full_sync = app._should_do_full_sync()

        assert count_mock.call_count == 1
        assert not full_sync

    @patch.object(App, '_sync', return_value=None)
    @patch.object(App, '_should_do_full_sync', return_value=True)
    @patch.object(DeeweeClient, 'max_last_modified_timestamp', return_value=datetime.now())
    def test_main_full(self, max_last_modified_timestamp_mock, should_do_full_sync_mock, sync_mock):
        app = App()
        app.main()

        assert sync_mock.call_count == 1
        assert should_do_full_sync_mock.call_count == 1
        assert max_last_modified_timestamp_mock.call_count == 0

        call_arg = sync_mock.call_args[0][0]
        assert call_arg is None

    @patch.object(App, '_sync', return_value=None)
    @patch.object(App, '_should_do_full_sync', return_value=False)
    @patch.object(DeeweeClient, 'max_last_modified_timestamp', return_value=datetime.now())
    def test_main_diff(self, max_last_modified_timestamp_mock, should_do_full_sync_mock, sync_mock):
        app = App()
        app.main()

        assert sync_mock.call_count == 1
        assert should_do_full_sync_mock.call_count == 1
        assert max_last_modified_timestamp_mock.call_count == 1

        call_arg = sync_mock.call_args[0][0]
        assert type(call_arg) == datetime

    @patch.object(LdapClient, 'search_ldap_orgs', return_value=['org1'])
    @patch.object(LdapClient, 'search_ldap_people', return_value=['person1'])
    @patch.object(DeeweeClient, 'upsert_ldap_results_many', return_value=None)
    def test_sync(self, upsert_ldap_results_many_mock, search_ldap_people_mock, search_ldap_orgs_mock):
        app = App()
        app._sync()

        assert search_ldap_orgs_mock.call_count == 1
        assert search_ldap_people_mock.call_count == 1
        assert upsert_ldap_results_many_mock.call_count == 1

        assert search_ldap_orgs_mock.call_args[0][0] is None
        assert search_ldap_people_mock.call_args[0][0] is None
        assert upsert_ldap_results_many_mock.call_args[0][0] == [(['org1'], 'org'), (['person1'], 'person')]

    @patch.object(App, '_should_do_full_sync', side_effect=PSQLError)
    def test_main_psql_error(self, should_do_full_sync_mock):
        app = App()
        with pytest.raises(PSQLError):
            app.main()

    @patch.object(App, '_sync', side_effect=LDAPExceptionError)
    @patch.object(App, '_should_do_full_sync', return_value=True)
    def test_main_ldap_error(self, should_do_full_sync_mock, sync_mock):
        app = App()
        with pytest.raises(LDAPExceptionError):
            app.main()
