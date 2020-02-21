from viaa.configuration import ConfigParser
from viaa.observability import logging

from ldap_communication import LdapClient
from deewee_communication import DeeweeClient


# Initialize the logger and the configuration
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class App:

    def __init__(self):

        # Initialize ldap and deewee clients
        self.ldap_client = LdapClient(config.config['ldap'])
        self.deewee_client = DeeweeClient(config.config['postgresql'])

    def _should_do_full_sync(self):
        """If the target table is empty, a full load is needed"""
        return self.deewee_client.count() == 0

    def _sync_full(self):
        # Orgs
        logger.info('Searching for orgs')
        ldap_results_orgs = self.ldap_client.search_ldap_orgs()
        logger.info(f'Found {len(ldap_results_orgs)} org(s) to sync')
        self.deewee_client.insert_ldap_results_many(ldap_results_orgs, 'org')

        # People
        logger.info('Searching for people')
        ldap_results_people = self.ldap_client.search_ldap_people()
        logger.info(f'Found {len(ldap_results_people)} people to sync')
        self.deewee_client.insert_ldap_results_many(ldap_results_people, 'person')

    def _sync_difference(self):
        last_modified_timestamp = self.deewee_client.max_last_modified_timestamp()

        # Orgs
        logger.info('Searching for orgs')
        ldap_results_orgs = self.ldap_client.search_ldap_orgs(last_modified_timestamp)
        new_orgs, to_update_orgs = self._split_new_update_entries(ldap_results_orgs)

        logger.info(f'Found {len(new_orgs)} org(s) to insert')
        self.deewee_client.insert_ldap_results_many(new_orgs, 'org')
        logger.info(f'Found {len(to_update_orgs)} org(s) to update')
        self.deewee_client.update_ldap_results(to_update_orgs)

        # People
        logger.info('Searching for people')
        ldap_results_people = self.ldap_client.search_ldap_people(last_modified_timestamp)
        new_people, to_update_people = self._split_new_update_entries(ldap_results_people)

        logger.info(f'Found {len(new_people)} new people to insert')
        self.deewee_client.insert_ldap_results_many(new_people, 'person')
        logger.info(f'Found {len(to_update_people)} people to update')
        self.deewee_client.update_ldap_results(to_update_people)

    def _split_new_update_entries(self, modified_entries: list) -> tuple:
        """Given the modified entries, calculate new and to-update entries

        Querying on the modified timestamp from LDAP returns the new and to-update entries.
        Check which entries actually exist in the database.and which not.
        Splits up the entries in a new entries list and a to-update entries list.

        Returns:
            tuple -- a list of new entries and a list of to-update entries
        """
        new_entries = []
        to_update_entries = []
        for modified_entry in modified_entries:
            if self.deewee_client.exists(modified_entry.entryUUID.value):
                to_update_entries.append(modified_entry)
            else:
                new_entries.append(modified_entry)
        return (new_entries, to_update_entries)

    def main(self):
        if self._should_do_full_sync():
            logger.info('Start full sync')
            self._sync_full()
        else:
            logger.info('Start sync of difference since last sync')
            self._sync_difference()


if __name__ == "__main__":
    App().main()
