REGISTRY=$1
BRANCH=$2
VERSION=$3

cp ./config.yml.example ./config.yml
docker build -t "${REGISTRY}/viaa-tools/ldap2deewee:${VERSION}" .
