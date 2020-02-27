import ldap3
from datetime import datetime
from functools import wraps


class LdapWrapper:
    """Allows for communicating with an LDAP server"""
    def __init__(self, params: dict, search_attributes: list = ldap3.ALL_ATTRIBUTES):
        self.params_ldap = params
        self.search_attributes = search_attributes

    def _connect_auth_ldap(function):
        """Wrapper function that connects and authenticates to the LDAP server.

        The passed function will receive the open connection.
        """
        @wraps(function)
        def wrapper_connect(self, *args, **kwargs):
            server = ldap3.Server(self.params_ldap['URI'])
            with ldap3.Connection(server, self.params_ldap['bind'], self.params_ldap['password'], auto_bind=True) as conn:
                val = function(self, connection=conn, *args, **kwargs)
            return val
        return wrapper_connect

    @_connect_auth_ldap
    def search(self, search_base: str, filter: str = '(objectClass=*)', connection=None):
        connection.search(search_base, filter, attributes=self.search_attributes)
        return connection.entries

    @_connect_auth_ldap
    def add(self, dn: str, object_class=None, attributes=None, connection=None):
        return connection.add(dn, object_class, attributes)

    @_connect_auth_ldap
    def delete(self, dn: str, connection=None):
        return connection.delete(dn)


class LdapClient:
    """Acts as a client to query relevant information from LDAP"""

    LDAP_SUFFIX = 'dc=hetarchief,dc=be'
    LDAP_PEOPLE_PREFIX = 'ou=people'
    LDAP_ORGS_PREFIX = 'ou=orgs'

    def __init__(self, params: dict):
        search_attributes = [ldap3.ALL_ATTRIBUTES, 'modifyTimestamp', 'entryUUID']
        self.ldap_wrapper = LdapWrapper(params, search_attributes)

    def _search_ldap(self, prefix: str, partial_filter: str, modified_at: datetime = None) -> list:
        # Format modify timestamp to an LDAP filter string
        modify_filter_string = '' if modified_at is None else f'(!(modifyTimestamp<={modified_at.strftime("%Y%m%d%H%M%SZ")}))'
        # Construct the LDAP filter string
        filter = f'(&(objectClass=*){partial_filter}{modify_filter_string})'
        return self.ldap_wrapper.search(f'{prefix},{self.LDAP_SUFFIX}', filter)

    def search_ldap_orgs(self, modified_at: datetime = None) -> list:
        return self._search_ldap(self.LDAP_ORGS_PREFIX, f'(!({self.LDAP_ORGS_PREFIX}))', modified_at)

    def search_ldap_people(self, modified_at: datetime = None) -> list:
        return self._search_ldap(self.LDAP_PEOPLE_PREFIX, f'(!({self.LDAP_PEOPLE_PREFIX}))', modified_at)
