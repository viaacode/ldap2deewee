REGISTRY=$1
BRANCH=$2
VERSION=$3

cp ./config.yml.example ./config.yml
docker build -t "${REGISTRY}/ldap2deewee:${BRANCH}-${VERSION}" .