import ldap3
from datetime import datetime


class LdapWrapper:
    """Allows for communicating with an LDAP server"""
    def __init__(self, params: dict, search_attributes: list = ldap3.ALL_ATTRIBUTES):
        self.params_ldap = params
        self.search_attributes = search_attributes

    def search(self, search_base: str, filter: str = '(objectClass=*)'):
        server = ldap3.Server(self.params_ldap['URI'])
        with ldap3.Connection(server, self.params_ldap['bind'], self.params_ldap['password'], auto_bind=True) as conn:
            conn.search(search_base, filter, attributes=self.search_attributes)
        return conn.entries


class LdapClient:
    """Acts as a client to query relevant information from LDAP"""
    LDAP_SUFFIX = ',dc=hetarchief,dc=be'

    def __init__(self, params: dict):
        search_attributes = [ldap3.ALL_ATTRIBUTES, 'modifyTimestamp', 'entryUUID']
        self.ldap_wrapper = LdapWrapper(params, search_attributes)

    def _search_ldap(self, prefix: str, partial_filter: str, modified_at: datetime = None) -> list:
        # Format modify timestamp to an LDAP filter string
        modify_filter_string = '' if modified_at is None else f'(!(modifyTimestamp<={modified_at.strftime("%Y%m%d%H%M%SZ")}))'
        # Construct the LDAP filter string
        filter = f'(&(objectClass=*){partial_filter}{modify_filter_string})'
        return self.ldap_wrapper.search(f'{prefix}{self.LDAP_SUFFIX}', filter)

    def search_ldap_orgs(self, modified_at: datetime = None) -> list:
        return self._search_ldap('ou=orgs', '(!(ou=orgs))', modified_at)

    def search_ldap_people(self, modified_at: datetime = None) -> list:
        return self._search_ldap('ou=people', '(!(ou=people))', modified_at)
