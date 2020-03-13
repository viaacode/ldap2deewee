REGISTRY=$1
IMAGE_NAME=$2

login_oc.sh https://c100-e.eu-de.containers.cloud.ibm.com:31240/
docker push "${REGISTRY}/${IMAGE_NAME}:latest"