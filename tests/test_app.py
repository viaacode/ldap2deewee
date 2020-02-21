from datetime import datetime

from app import App


def test_main_full_sync():
    app = App()
    # Truncate to force a full load
    app.deewee_client.truncate_table()
    assert app.deewee_client.count_type('org') == 0
    assert app.deewee_client.count_type('person') == 0
    app.main()
    assert app.deewee_client.count_type('org') > 0
    assert app.deewee_client.count_type('person') > 0


def test_main_sync_none():
    app = App()
    app.deewee_client.truncate_table()
    # Add a row with a created and modified timestamps after the values in LDAP
    app.deewee_client.insert_entity()
    assert app.deewee_client.count() == 1
    # Should not sync anything
    app.main()
    assert app.deewee_client.count() == 1


def test_main_sync():
    app = App()
    table_name = app.deewee_client.TABLE_NAME
    app.deewee_client.truncate_table()
    # Add a row with a created and modified timestamps before the values in LDAP
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
