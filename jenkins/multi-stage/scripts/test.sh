REGISTRY=$1
BRANCH=$2
VERSION=$3

docker container run --name ldap2deewee_builder_test "${REGISTRY}/ldap2deewee_test:${BRANCH}-${VERSION}"