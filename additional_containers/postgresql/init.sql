CREATE TABLE IF NOT EXISTS entities(
    id serial PRIMARY KEY,
    ldap_uuid UUID NOT NULL UNIQUE,
    type VARCHAR,
    content JSON,
    last_modified_timestamp timestamp
);