import pytest
import ldap3
from datetime import timedelta

from viaa.configuration import ConfigParser

from ldap_communication import LdapWrapper, LdapClient


class TestLdapWrapper:
    @pytest.fixture
    def ldap_wrapper(self):
        """Returns a LdapWrapper initiliazed by the parameters in config.yml"""
        return LdapWrapper(ConfigParser().config['ldap'])

    def test_search(self, ldap_wrapper):
        search_result = ldap_wrapper.search('ou=orgs,dc=hetarchief,dc=be')
        assert search_result is not None

    def test_search_invalid_password(self):
        params = ConfigParser().config['ldap']
        params['password'] = 'invalid'
        ldap_wrapper = LdapWrapper(params)

        with pytest.raises(ldap3.core.exceptions.LDAPBindError) as ldap_error:
            ldap_wrapper.search('ou=people,dc=hetarchief,dc=be')
        assert ldap_error.value.args[0] is not None

    def test_search_invalid_search(self, ldap_wrapper):
        with pytest.raises(ldap3.core.exceptions.LDAPInvalidDnError) as ldap_error:
            ldap_wrapper.search('invalid')
        assert ldap_error.value.args[0] is not None


class TestLdapClient:

    @pytest.fixture
    def ldap_client(self):
        """Returns a LdapClient initiliazed by the parameters in config.yml"""
        return LdapClient(ConfigParser().config['ldap'])

    def _modifytimestamp_value(self, ldap_entry):
        """Returns the modifyTimestamp value of the LDAP entry"""
        return ldap_entry.modifyTimestamp.value

    def test_search_ldap_orgs(self, ldap_client):
        ldap_orgs = ldap_client.search_ldap_orgs()
        assert len(ldap_orgs) > 0  # Asserts list not empty
        max_timestamp = max(ldap_orgs, key=self._modifytimestamp_value).modifyTimestamp.value
        # Timestamp greater than last modified should result in no results
        search_timestamp = max_timestamp + timedelta(microseconds=1)
        assert len(ldap_client.search_ldap_orgs(search_timestamp)) == 0  # Asserts list empty
        # Timestamp lesser than last modified should result in some results
        search_timestamp = max_timestamp - timedelta(microseconds=1)
        assert len(ldap_client.search_ldap_orgs(search_timestamp)) > 0  # Asserts list not empty

    def test_search_ldap_people(self, ldap_client):
        ldap_people = ldap_client.search_ldap_people()
        assert len(ldap_people) > 0  # Asserts list not empty
        max_timestamp = max(ldap_people, key=self._modifytimestamp_value).modifyTimestamp.value
        # Timestamp  greater than last modified returns no results
        search_timestamp = max_timestamp + timedelta(microseconds=1)
        assert len(ldap_client.search_ldap_people(search_timestamp)) == 0  # Asserts list empty
        # Timestamp lesser than last modified returns some results
        search_timestamp = max_timestamp - timedelta(microseconds=1)
        assert len(ldap_client.search_ldap_people(search_timestamp)) > 1  # Asserts list not empty
