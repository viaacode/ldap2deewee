import pytest
from ldap3.core.exceptions import LDAPBindError

from datetime import datetime

from app import App


@pytest.fixture
def app():
    """Returns a instance of App.

    Also truncates the PostgreSQL table in order to start with a clean slate."""
    app = App()
    app.deewee_client.truncate_table()
    return app


def test_main_full_sync(app):
    assert app.deewee_client.count_type('org') == 0
    assert app.deewee_client.count_type('person') == 0
    app.main()
    assert app.deewee_client.count_type('org') > 0
    assert app.deewee_client.count_type('person') > 0


def test_main_sync_none(app):
    # Add a row with modified timestamp after the highest value in LDAP
    app.deewee_client.insert_entity()
    assert app.deewee_client.count() == 1
    # Should not sync anything
    app.main()
    assert app.deewee_client.count() == 1


def test_main_sync(app):
    table_name = app.deewee_client.TABLE_NAME
    # Add a row with a modified timestamp before highest value in LDAP
    app.deewee_client.insert_entity(datetime(1970, 1, 1))
    assert app.deewee_client.count() == 1
    # Should insert the new ones
    app.main()
    count = app.deewee_client.count()
    assert count > 1
    # Change last_modified_timestamp so next run should do an update sync
    sql = f'UPDATE {table_name} SET last_modified_timestamp = %s, content = NULL;'
    app.deewee_client.postgresql_wrapper.execute(sql, (datetime(1970, 1, 1),))
    app.main()
    assert app.deewee_client.count() == count  # No new ones
    assert app.deewee_client.count_where('content is NULL') == 1


def test_main_ldap_invalid_password(app):
    assert app.deewee_client.count() == 0
    app.ldap_client.ldap_wrapper.params_ldap['password'] = 'invalid'
    with pytest.raises(LDAPBindError) as _:
        app.main()
    assert app.deewee_client.count() == 0
