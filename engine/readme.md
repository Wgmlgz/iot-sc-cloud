docker compose up --build --force-recreate



yc container registry configure-docker


docker build . -t engine
docker run --env-file .env -p 5000:5000 engine

docker tag engine cr.yandex/crp7tvvisbkjh1cc5ccg/engine
docker push  cr.yandex/crp7tvvisbkjh1cc5ccg/engine
