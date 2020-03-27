REGISTRY=$1
BRANCH=$2
VERSION=$3

docker container run --name ldap2deewee_builder_lint "${REGISTRY}/ldap2deewee_lint:${BRANCH}-${VERSION}"
