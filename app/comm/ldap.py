#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ldap3
from datetime import datetime
from functools import wraps


LDAP_SUFFIX = 'dc=hetarchief,dc=be'
LDAP_PEOPLE_PREFIX = 'ou=people'
LDAP_ORGS_PREFIX = 'ou=orgs'
SEARCH_ATTRIBUTES = [ldap3.ALL_ATTRIBUTES, 'modifyTimestamp', 'entryUUID']


class LdapWrapper:
    """Allows for communicating with an LDAP server"""

    def __init__(self, params: dict, search_attributes=ldap3.ALL_ATTRIBUTES,
                 get_info=ldap3.SCHEMA, client_strategy=ldap3.SYNC):
        self.search_attributes = search_attributes

        # These can potentially be absent so that anonymous access is allowed
        user = params.get('bind')
        password = params.get('password')

        server = ldap3.Server(params['URI'], get_info=get_info)
        self.connection = ldap3.Connection(
            server, user, password, client_strategy=client_strategy
        )

    def _connect_auth_ldap(function):
        """Wrapper function that connects and authenticates to the LDAP server.

        The passed function will receive the open connection.
        """
        @wraps(function)
        def wrapper_connect(self, *args, **kwargs):
            try:
                self.connection.bind()
                val = function(self, *args, **kwargs)
            except ldap3.core.exceptions.LDAPException as exception:
                raise exception
            finally:
                self.connection.unbind()
            return val
        return wrapper_connect

    @_connect_auth_ldap
    def search(self, search_base: str, filter: str = '(objectClass=*)'):
        self.connection.search(
            search_base, filter, attributes=self.search_attributes
        )
        return self.connection.entries

    @_connect_auth_ldap
    def add(self, dn: str, object_class=None, attributes=None):
        return self.connection.add(dn, object_class, attributes)

    @_connect_auth_ldap
    def delete(self, dn: str):
        return self.connection.delete(dn)


class LdapClient:
    """Acts as a client to query relevant information from LDAP"""

    def __init__(self, params: dict,):
        self.ldap_wrapper = LdapWrapper(params, SEARCH_ATTRIBUTES)

    def _search(self, prefix: str, partial_filter: str, modified_at: datetime = None) -> list:
        # Format modify timestamp to an LDAP filter string
        modify_filter_string = (
            ''
            if modified_at is None
            else f'(!(modifyTimestamp<={modified_at.strftime("%Y%m%d%H%M%SZ")}))'
        )
        # Construct the LDAP filter string
        filter = f'(&(objectClass=*){partial_filter}{modify_filter_string})'
        return self.ldap_wrapper.search(f'{prefix},{LDAP_SUFFIX}', filter)

    def search_orgs(self, modified_at: datetime = None) -> list:
        return self._search(
            LDAP_ORGS_PREFIX, f'(!({LDAP_ORGS_PREFIX}))', modified_at
        )

    def search_people(self, modified_at: datetime = None) -> list:
        return self._search(
            LDAP_PEOPLE_PREFIX, f'(!({LDAP_PEOPLE_PREFIX}))', modified_at
        )
