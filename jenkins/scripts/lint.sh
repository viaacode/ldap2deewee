REGISTRY=$1
BRANCH=$2
VERSION=$3

docker container run --name ldap2deewee_lint --entrypoint flake8 "${REGISTRY}/ldap2deewee:${BRANCH}-${VERSION}" --exit-zero
