REGISTRY=$1
BRANCH=$2
VERSION=$3

docker container run --name ldap2deewee_test "${REGISTRY}/ldap2deewee:${BRANCH}-${VERSION}" "-m" "pytest" "tests"