import pytest
import ldap3
from datetime import timedelta
import time

from viaa.configuration import ConfigParser

from ldap_communication import LdapWrapper, LdapClient

LDAP_SUFFIX = 'dc=hetarchief,dc=be'
LDAP_PEOPLE = f'ou=people,{LDAP_SUFFIX}'
LDAP_ORGS = f'ou=orgs,{LDAP_SUFFIX}'
DN_ORG1 = f'o=meemoo_org1,{LDAP_ORGS}'
DN_ORG2 = f'o=meemoo_org2,{LDAP_ORGS}'
DN_PERSON1 = f'mail=meemoo_user1@meemoo.meemoo,{LDAP_PEOPLE}'
DN_PERSON2 = f'mail=meemoo_user2@meemoo.meemoo,{LDAP_PEOPLE}'


class TestLdapWrapper:

    @pytest.fixture
    def ldap_wrapper(self):
        """Returns a LdapWrapper initiliazed by the parameters in config.yml"""
        return LdapWrapper(ConfigParser().config['ldap'])

    def test_search(self, ldap_wrapper):
        search_result = ldap_wrapper.search(LDAP_ORGS)
        assert search_result is not None

    def test_search_invalid_password(self):
        params = ConfigParser().config['ldap']
        params['password'] = 'invalid'
        ldap_wrapper = LdapWrapper(params)

        with pytest.raises(ldap3.core.exceptions.LDAPBindError) as ldap_error:
            ldap_wrapper.search(LDAP_PEOPLE)
        assert ldap_error.value.args[0] is not None

    def test_search_invalid_search(self, ldap_wrapper):
        with pytest.raises(ldap3.core.exceptions.LDAPInvalidDnError) as ldap_error:
            ldap_wrapper.search('invalid')
        assert ldap_error.value.args[0] is not None

    def test_add_invalid(self, ldap_wrapper):
        with pytest.raises(ldap3.core.exceptions.LDAPInvalidDnError) as ldap_error:
            ldap_wrapper.add('dn')
        assert ldap_error.value.args[0] is not None

    def test_add_delete(self, ldap_wrapper):
        dn = f'o=test1,{LDAP_ORGS}'
        add_result = ldap_wrapper.add(dn, 'organization', {'o': 'test1'})
        assert add_result
        delete_result = ldap_wrapper.delete(f'o=test1,{LDAP_ORGS}')
        assert delete_result


class TestLdapClient:
    """Tests if the client can communicate properly with the LDAP server.

    The tests are independent of existing state on the LDAP server.
    """

    @classmethod
    def setup_class(cls):
        """ Create two orgs and two people"""
        ldap_wrapper = LdapWrapper(ConfigParser().config['ldap'])
        ldap_wrapper.add(DN_ORG1, 'organization', {'o': 'meemoo_org1'})
        time.sleep(1)  # Wait a bit to ensure later modifyTimestamp
        ldap_wrapper.add(DN_ORG2, 'organization', {'o': 'meemoo_org2'})

        ldap_wrapper.add(DN_PERSON1, 'inetOrgPerson', {'mail': 'meemoo_user1@meemoo.meemoo', 'cn': 'meemoo1', 'sn': 'meemoo1'})
        time.sleep(1)  # Wait a bit to ensure later modifyTimestamp
        ldap_wrapper.add(DN_PERSON2, 'inetOrgPerson', {'mail': 'meemoo_user2@meemoo.meemoo', 'cn': 'meemoo2', 'sn': 'meemoo2'})

    @classmethod
    def teardown_class(cls):
        """ Remove the orgs and people to not pollute the LDAP server"""
        ldap_wrapper = LdapWrapper(ConfigParser().config['ldap'])
        ldap_wrapper.delete(DN_ORG1)
        ldap_wrapper.delete(DN_ORG2)

        ldap_wrapper.delete(DN_PERSON1)
        ldap_wrapper.delete(DN_PERSON2)

    @pytest.fixture
    def ldap_client(self):
        """Returns a LdapClient initiliazed by the parameters in config.yml"""
        return LdapClient(ConfigParser().config['ldap'])

    def _modifytimestamp_value(self, ldap_entry):
        """Returns the modifyTimestamp value of the LDAP entry"""
        return ldap_entry.modifyTimestamp.value

    def test_search_ldap_orgs(self, ldap_client):
        ldap_orgs = ldap_client.search_ldap_orgs()
        assert len(ldap_orgs) >= 2
        assert any(ldap_entry.entry_dn == DN_ORG2 for ldap_entry in ldap_orgs)

        max_timestamp = max(ldap_orgs, key=self._modifytimestamp_value).modifyTimestamp.value
        # Timestamp greater than last modified should result in no results
        search_timestamp = max_timestamp + timedelta(microseconds=1)
        assert len(ldap_client.search_ldap_orgs(search_timestamp)) == 0  # Asserts list empty

        # Timestamp lesser than last modified should result in DN_ORG2
        search_timestamp = max_timestamp - timedelta(microseconds=1)
        ldap_orgs_filtered = ldap_client.search_ldap_orgs(search_timestamp)
        assert len(ldap_orgs_filtered) == 1
        assert ldap_orgs_filtered[0].entry_dn == DN_ORG2

    def test_search_ldap_people(self, ldap_client):
        ldap_people = ldap_client.search_ldap_people()

        assert len(ldap_people) >= 2
        assert any(ldap_entry.entry_dn == DN_PERSON2 for ldap_entry in ldap_people)

        max_timestamp = max(ldap_people, key=self._modifytimestamp_value).modifyTimestamp.value
        # Timestamp greater than last modified should result in no results
        search_timestamp = max_timestamp + timedelta(microseconds=1)
        assert len(ldap_client.search_ldap_people(search_timestamp)) == 0  # Asserts list empty

        # Timestamp lesser than last modified should result in DN_PERSON2
        search_timestamp = max_timestamp - timedelta(microseconds=1)
        ldap_people_filtered = ldap_client.search_ldap_people(search_timestamp)
        assert len(ldap_people_filtered) == 1
        assert ldap_people_filtered[0].entry_dn == DN_PERSON2
