#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import ldap3
from datetime import timedelta, datetime
import time
import copy

from viaa.configuration import ConfigParser

from app.comm.ldap import (
    LdapWrapper,
    LdapClient,
    SEARCH_ATTRIBUTES,
    LDAP_PEOPLE_PREFIX,
    LDAP_ORGS_PREFIX
)


LDAP_SUFFIX = 'dc=hetarchief,dc=be'
LDAP_PEOPLE = f'{LDAP_PEOPLE_PREFIX},{LDAP_SUFFIX}'
LDAP_ORGS = f'o{LDAP_ORGS_PREFIX},{LDAP_SUFFIX}'
DN_ORG1 = f'o=meemoo_org1,{LDAP_ORGS}'
DN_ORG2 = f'o=meemoo_org2,{LDAP_ORGS}'
DN_PERSON1 = f'mail=meemoo_user1@meemoo.meemoo,{LDAP_PEOPLE}'
DN_PERSON2 = f'mail=meemoo_user2@meemoo.meemoo,{LDAP_PEOPLE}'
ldap_config_dict = ConfigParser().config['ldap']


class LdapWrapperMock(LdapWrapper):

    def __init__(self, params: dict, search_attributes=ldap3.ALL_ATTRIBUTES):
        super().__init__(
            params, get_info=ldap3.OFFLINE_SLAPD_2_4, client_strategy=ldap3.MOCK_SYNC
        )
        user = params.get('bind')
        password = params.get('password')
        # Allow for anonymous access
        if user is not None and password is not None:
            self.connection.strategy.add_entry(
                user, {'userPassword': password, 'sn': 'admin_sn'}
            )


class LdapClientMock(LdapClient):

    def __init__(self, params: dict):
        self.ldap_wrapper = LdapWrapperMock(params, SEARCH_ATTRIBUTES)


class TestLdapWrapperMock:

    @pytest.fixture
    def ldap_wrapper(self):
        """Returns a LdapWrapperMock initiliazed by the parameters in config.yml"""
        return LdapWrapperMock(ldap_config_dict)

    def test_search(self, ldap_wrapper):
        search_result = ldap_wrapper.search(LDAP_ORGS)
        assert search_result is not None

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


class TestLdapWrapperMockAnonymous(TestLdapWrapperMock):

    @pytest.fixture
    def ldap_wrapper(self):
        """Returns a LdapWrapperMock with anonymous access.

        Non-credentials parameters are parsed from the config.yml file.
        """
        ldap_config_dict_anonymous = copy.deepcopy(ldap_config_dict)
        del ldap_config_dict_anonymous['bind']
        del ldap_config_dict_anonymous['password']
        return LdapWrapperMock(ldap_config_dict_anonymous)


class TestLdapClientMock:
    """Tests if the client can communicate with an LDAP mock server"""

    @classmethod
    def setup_class(cls):
        """ Create two orgs and two people"""
        cls.ldap_client = LdapClientMock(ldap_config_dict)
        ldap_wrapper = cls.ldap_client.ldap_wrapper
        ldap_wrapper.add(
            DN_ORG1,
            'organization',
            {'o': 'meemoo_org1', 'modifyTimestamp': datetime.now()}
        )
        time.sleep(1)
        ldap_wrapper.add(
            DN_ORG2, 'organization',
            {'o': 'meemoo_org2', 'modifyTimestamp': datetime.now()}
        )

        ldap_wrapper.add(
            DN_PERSON1,
            'inetOrgPerson',
            {
                'mail': 'meemoo_user1@meemoo.meemoo',
                'cn': 'meemoo1',
                'sn': 'meemoo1',
                'modifyTimestamp': datetime.now()
            }
        )
        time.sleep(1)
        ldap_wrapper.add(
            DN_PERSON2,
            'inetOrgPerson',
            {
                'mail': 'meemoo_user2@meemoo.meemoo',
                'cn': 'meemoo2',
                'sn': 'meemoo2',
                'modifyTimestamp': datetime.now()
            }
        )

    def _modifytimestamp_value(self, ldap_entry):
        """Returns the modifyTimestamp value of the LDAP entry"""
        return ldap_entry.modifyTimestamp.value

    def test_search_orgs(self):
        ldap_orgs = self.ldap_client.search_orgs()
        assert len(ldap_orgs) == 2
        assert any(ldap_entry.entry_dn == DN_ORG2 for ldap_entry in ldap_orgs)

        last_modified_entry = max(ldap_orgs, key=self._modifytimestamp_value)
        max_timestamp = last_modified_entry.modifyTimestamp.value
        # Timestamp greater than last modified should result in no results
        search_timestamp = max_timestamp + timedelta(microseconds=1)
        assert len(self.ldap_client.search_orgs(search_timestamp)) == 0

        # Timestamp lesser than last modified should result in DN_ORG2
        search_timestamp = max_timestamp - timedelta(microseconds=1)
        ldap_orgs_filtered = self.ldap_client.search_orgs(search_timestamp)
        assert len(ldap_orgs_filtered) == 1
        assert ldap_orgs_filtered[0].entry_dn == DN_ORG2

    def test_search_people(self):
        ldap_people = self.ldap_client.search_people()

        assert len(ldap_people) == 2
        assert any(ldap_entry.entry_dn == DN_PERSON2 for ldap_entry in ldap_people)

        last_modified_entry = max(ldap_people, key=self._modifytimestamp_value)
        max_timestamp = last_modified_entry.modifyTimestamp.value
        # Timestamp greater than last modified should result in no results
        search_timestamp = max_timestamp + timedelta(microseconds=1)
        assert len(self.ldap_client.search_people(search_timestamp)) == 0

        # Timestamp lesser than last modified should result in DN_PERSON2
        search_timestamp = max_timestamp - timedelta(microseconds=1)
        ldap_people_filtered = self.ldap_client.search_people(search_timestamp)
        assert len(ldap_people_filtered) == 1
        assert ldap_people_filtered[0].entry_dn == DN_PERSON2
