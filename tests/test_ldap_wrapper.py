import pytest
import ldap3

from viaa.configuration import ConfigParser

from ldap_communication import LdapWrapper


@pytest.fixture
def ldap_wrapper():
    """Returns a LdapWrapper initiliazed by the parameters in config.yml"""
    return LdapWrapper(ConfigParser().config['ldap'])


def test_search(ldap_wrapper):
    search_result = ldap_wrapper.search('ou=orgs,dc=hetarchief,dc=be')
    assert search_result is not None


def test_search_invalid_password():
    params = ConfigParser().config['ldap']
    params['password'] = 'invalid'
    ldap_wrapper = LdapWrapper(params)

    with pytest.raises(ldap3.core.exceptions.LDAPBindError) as ldap_error:
        ldap_wrapper.search('ou=people,dc=hetarchief,dc=be')
    assert ldap_error.value.args[0] is not None


def test_search_invalid_search(ldap_wrapper):
    with pytest.raises(ldap3.core.exceptions.LDAPInvalidDnError) as ldap_error:
        ldap_wrapper.search('invalid')
    assert ldap_error.value.args[0] is not None
