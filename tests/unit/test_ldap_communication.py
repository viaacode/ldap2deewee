#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import patch
from datetime import datetime

from viaa.configuration import ConfigParser

from app.ldap_communication import LdapWrapper, LdapClient


class TestLdapWrapper:

    @pytest.fixture
    @patch('ldap3.Connection')
    def ldap_wrapper(self, mock_connection):
        """Returns a LdapWrapper initiliazed by the parameters in config.yml"""
        return LdapWrapper(ConfigParser().config['ldap'])

    def test_search(self, ldap_wrapper):
        ldap_wrapper.connection.entries.return_value = 'entry'
        result = ldap_wrapper.search('orgs')
        mock = ldap_wrapper.connection
        assert mock.search.call_args[0][0] == 'orgs'
        assert mock.search.call_count == 1
        assert result.return_value == 'entry'

    def test_add(self, ldap_wrapper):
        ldap_wrapper.connection.add.return_value = True
        result = ldap_wrapper.add('dn')
        mock = ldap_wrapper.connection
        assert mock.add.call_args[0][0] == 'dn'
        assert mock.add.call_count == 1
        assert result

    def test_delete(self, ldap_wrapper):
        ldap_wrapper.connection.delete.return_value = True
        result = ldap_wrapper.delete('dn')
        mock = ldap_wrapper.connection
        assert mock.delete.call_args[0][0] == 'dn'
        assert mock.delete.call_count == 1
        assert result


class TestLdapClient:

    @patch('app.ldap_communication.LdapWrapper')
    @patch.object(LdapClient, '_search', return_value=None)
    def test_search_orgs(self, _search_mock, ldap_wrapper):
        dt = datetime.now()
        ldap_client = LdapClient({})
        ldap_client.search_orgs(dt)
        assert _search_mock.call_count == 1
        assert _search_mock.call_args[0][0] == 'ou=orgs'
        assert _search_mock.call_args[0][1] == '(!(ou=orgs))'
        assert _search_mock.call_args[0][2] == dt

    @patch('app.ldap_communication.LdapWrapper')
    @patch.object(LdapClient, '_search', return_value=None)
    def test_search_people(self, _search_mock, ldap_wrapper):
        dt = datetime.now()
        ldap_client = LdapClient({})
        ldap_client.search_people(dt)
        assert _search_mock.call_count == 1
        assert _search_mock.call_args[0][0] == 'ou=people'
        assert _search_mock.call_args[0][1] == '(!(ou=people))'
        assert _search_mock.call_args[0][2] == dt

    @patch('app.ldap_communication.LdapWrapper')
    def test_search(self, ldap_wrapper_mock):
        prefix = 'prefix'
        partial_filter = 'partial'
        dt = datetime(2020, 2, 2)
        ldap_client = LdapClient({})
        ldap_client._search(prefix, partial_filter, dt)
        assert ldap_wrapper_mock.return_value.search.call_count == 1

        expected_search = f'{prefix},dc=hetarchief,dc=be'
        expected_filter = f'(&(objectClass=*){partial_filter}(!(modifyTimestamp<=20200202000000Z)))'
        assert ldap_wrapper_mock.return_value.search.call_args[0][0] == expected_search
        assert ldap_wrapper_mock.return_value.search.call_args[0][1] == expected_filter
