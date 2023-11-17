BACKEND_CONTAINER := gumsup4_api:latest
DEV_BACKEND_CONTAINER := gumsup4_api_dev

COMPOSE = docker-compose -f docker/docker-compose.yml
WAIT_FOR_DB = wait-for-it --service gumsup4_db:5432


.PHONY: build test lint migrations format


test: build
	docker-compose -f docker/docker-compose.test.yml \
	  run gumsup4_web \
	  /bin/bash -c \
	  "${WAIT_FOR_DB} && pytest"

lint:
	docker run --rm ${DEV_BACKEND_CONTAINER} black --exclude frontend --check .

shell:
	$(COMPOSE) run gumsup4_web /bin/bash

format:
	docker run --rm -v "${PWD}:/src/app" ${DEV_BACKEND_CONTAINER} black .

build:
	docker build -t ${BACKEND_CONTAINER} -f docker/Dockerfile.api .
	docker build -t ${DEV_BACKEND_CONTAINER} \
	  --build-arg REQUIREMENTS=requirements.dev.txt \
	  -f docker/Dockerfile.api .

teardown:
	$(COMPOSE) down -v

start:
	$(COMPOSE) up

makemigrations:
	$(COMPOSE) run --rm gumsup4_web python manage.py makemigrations

migrate:
	$(COMPOSE) run --rm gumsup4_web python manage.py migrate
