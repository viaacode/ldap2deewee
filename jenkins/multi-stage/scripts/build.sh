REGISTRY=$1
BRANCH=$2
VERSION=$3

cp ./config.yml.example ./config.yml
docker build -t Dockerfile_multi --target builder "${REGISTRY}/ldap2deewee_builder:${BRANCH}-${VERSION}" .
docker build -f Dockerfile_multi --target app -t "${REGISTRY}/ldap2deewee_app:${BRANCH}-${VERSION}" .
docker build -f Dockerfile_multi --target test -t "${REGISTRY}/ldap2deewee_test:${BRANCH}-${VERSION}" .
docker build -f Dockerfile_multi --target lint -t "${REGISTRY}/ldap2deewee_lint:${BRANCH}-${VERSION}" .