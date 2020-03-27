REGISTRY=$1
IMAGE_NAME=$2
VERSION=$3

cp ./config.yml.example ./config.yml
docker build -t "${REGISTRY}/${IMAGE_NAME}:${VERSION}" .