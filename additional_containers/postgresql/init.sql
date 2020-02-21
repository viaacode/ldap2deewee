CREATE TYPE entity_type AS ENUM ('org', 'person');
CREATE TABLE entities(
    id serial PRIMARY KEY,
    ldap_uuid UUID,
    type entity_type,
    content JSON,
    last_modified_timestamp timestamp
);