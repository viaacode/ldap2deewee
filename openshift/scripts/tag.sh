REGISTRY=$1
IMAGE_NAME=$2
VERSION=$3

docker tag "${REGISTRY}/${IMAGE_NAME}:${VERSION}" "${REGISTRY}/${IMAGE_NAME}:latest"