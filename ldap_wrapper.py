import ldap3


class LdapWrapper:
    """Allows for communicating with an LDAP server"""
    def __init__(self, params: dict):
        self.params_ldap = params

    def search(self, search_base: str, filter: str = '(objectClass=*)'):
        server = ldap3.Server(self.params_ldap['URI'])
        with ldap3.Connection(server, self.params_ldap['bind'], self.params_ldap['password'], auto_bind=True) as conn:
            conn.search(search_base, filter, attributes=ldap3.ALL_ATTRIBUTES)
        return conn.entries
