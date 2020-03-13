REGISTRY=$1
IMAGE_NAME=$2
VERSION=$3

docker container run --name ldap2deewee_lint --entrypoint flake8 "${REGISTRY}/${IMAGE_NAME}:${VERSION}" --exit-zero
