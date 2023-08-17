mkdir tgi_data;

model=tiiuae/falcon-7b-instruct
volume=$PWD/tgi_data # share a volume with the Docker container to avoid downloading weights every run

docker run --gpus all --shm-size 1g -p 8080:8234 -v $volume:/data ghcr.io/huggingface/text-generation-inference:1.0.1 --model-id $model