REGISTRY=$1
IMAGE_NAME=$2

docker push "${REGISTRY}/${IMAGE_NAME}:latest"