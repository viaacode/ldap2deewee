REGISTRY=$1
IMAGE_NAME=$2
VERSION=$3

docker container run --name ldap2deewee_test "${REGISTRY}/${IMAGE_NAME}:${VERSION}" \
    "-m" "pytest" "--cov=app.app" "--cov=app.comm"