#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from ldap3.core.exceptions import LDAPExceptionError
from psycopg2 import OperationalError as PSQLError

from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.ldap_communication import LdapClient
from app.deewee_communication import DeeweeClient


# Initialize the logger and the configuration
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class App:

    def __init__(self):
        # Initialize ldap and deewee clients
        self.ldap_client = LdapClient(config.config["ldap"])
        self.deewee_client = DeeweeClient(config.config["postgresql"])

    def _sync(self, modified_since: datetime = None):
        """"Will sync the information in LDAP to the PostgreSQL DB.

        Executes an LDAP search per type.
        Those results will be send through in one transaction.
        If the transaction fails, rollback so that the DB will not be in an incomplete state.

        Arguments:
            modified_since -- Searches the LDAP results based on this parameter.
                              If None, it will retrieve all LDAP entries.
        """

        # Orgs
        logger.info("Searching for orgs")
        ldap_orgs = self.ldap_client.search_orgs(modified_since)
        logger.info(f"Found {len(ldap_orgs)} org(s) to sync")

        # People
        logger.info("Searching for people")
        ldap_people = self.ldap_client.search_people(modified_since)
        logger.info(f"Found {len(ldap_people)} people to sync")

        self.deewee_client.upsert_ldap_results_many(
            [(ldap_orgs, "org"), (ldap_people, "person")]
        )

    def main(self):
        try:
            modified_since = self.deewee_client.max_last_modified_timestamp()
            if modified_since is None:
                logger.info("Start full sync")
            else:
                logger.info(
                    f"Start sync of difference since last sync - {modified_since.isoformat()}"
                )
            self._sync(modified_since)
        except (PSQLError, LDAPExceptionError) as e:
            logger.error(e)
            raise e
        logger.info("sync successful")


if __name__ == "__main__":
    App().main()
