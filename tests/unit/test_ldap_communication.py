import pytest
from unittest.mock import patch

from viaa.configuration import ConfigParser

from ldap_communication import LdapWrapper


class TestLdapWrapper:

    @pytest.fixture
    def ldap_wrapper(self):
        """Returns a LdapWrapper initiliazed by the parameters in config.yml"""
        return LdapWrapper(ConfigParser().config['ldap'])

    @patch('ldap3.Connection')
    def test_search(self, mock_connection, ldap_wrapper):
        mock = mock_connection.return_value.__enter__.return_value
        mock.entries.return_value = 'entry'
        result = ldap_wrapper.search('orgs')
        mock = mock_connection.return_value.__enter__.return_value
        assert mock.search.call_args[0][0] == 'orgs'
        assert mock.search.call_count == 1
        assert result.return_value == 'entry'

    @patch('ldap3.Connection')
    def test_add(self, mock_connection, ldap_wrapper):
        mock_connection.return_value.add.return_value = True
        result = ldap_wrapper.add('dn')
        mock = mock_connection.return_value.__enter__.return_value
        assert mock.add.call_args[0][0] == 'dn'
        assert mock.add.call_count == 1
        assert result.return_value

    @patch('ldap3.Connection')
    def test_delete(self, mock_connection, ldap_wrapper):
        mock_connection.return_value.delete.return_value = True
        result = ldap_wrapper.delete('dn')
        mock = mock_connection.return_value.__enter__.return_value
        assert mock.delete.call_args[0][0] == 'dn'
        assert mock.delete.call_count == 1
        assert result.return_value
