from viaa.configuration import ConfigParser
from viaa.observability import logging

from ldap_wrapper import LdapWrapper
from postgresql_wrapper import PostgresqlWrapper


# Initialize the logger and the configuration
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)

# Initialize ldap and posgresql wrappers
ldap_wrapper = LdapWrapper(config.config['ldap'])
posgresql_wrapper = PostgresqlWrapper(config.config['postgresql'])

ARCHIEFBE_SUFFIX = ',dc=hetarchief,dc=be'
INSERT_QUERY = 'INSERT INTO entities (dn, type, content) VALUES (%s, %s, %s)'


def insert_ldap_results_in_deewee_many(ldap_results: list, type):
    # Parse the SQL values from the ldap results as a passable list
    values = [(ldap_result.entry_dn, type, ldap_result.entry_to_json()) for ldap_result in ldap_results]
    posgresql_wrapper.executemany(INSERT_QUERY, values)


def insert_ldap_results_in_deewee(ldap_results: list, type):
    for ldap_result in ldap_results:
        posgresql_wrapper.execute(INSERT_QUERY, (ldap_result.entry_dn, type, ldap_result.entry_to_json()))


def search_ldap(prefix: str, filter: str):
    return ldap_wrapper.search(prefix + ARCHIEFBE_SUFFIX, filter)


def main():
    # Orgs
    logger.info('Searching for orgs')
    ldap_results_orgs = search_ldap('ou=orgs', '(&(objectClass=*)(!(ou=orgs)))')
    logger.info(f'Found {len(ldap_results_orgs)} orgs to sync')
    insert_ldap_results_in_deewee_many(ldap_results_orgs, 'org')

    # People
    logger.info('Searching for people')
    ldap_results_people = search_ldap('ou=people', '(&(objectClass=*)(!(ou=people)))')
    logger.info(f'Found {len(ldap_results_people)} people to sync')
    insert_ldap_results_in_deewee_many(ldap_results_people, 'person')


if __name__ == "__main__":
    main()
