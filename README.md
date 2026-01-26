To compile locally: sudo docker build -t keepalive-tool .
To compile both for arm and linux: 
    docker buildx create --name mybuilder --use
    docker buildx inspect --bootstrap
To push: docker buildx build --platform linux/amd64,linux/arm64 -t follen99/keepalive-tool:latest --push .