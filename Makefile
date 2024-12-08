DOCKER_IMAGE_NAME=rabbitmqalertdev
DOCKER_COMPOSE_FILE="`pwd`/dev/docker-compose.yaml"
DOCKER_COMPOSE_PROJECT=rmqalert-dev
DOCKER_COMPOSE_CMD=docker compose -p $(DOCKER_COMPOSE_PROJECT) -f $(DOCKER_COMPOSE_FILE)

precommit:
	@pre-commit run --all-files

# Example: make bump patch
bump:
	@bump2version --config-file .bumpversion.cfg --allow-dirty $(filter-out $@,$(MAKECMDGOALS))

build:
	@docker build -t ${DOCKER_IMAGE_NAME} .

bash: build
	@docker run \
		-v "`pwd`:/code" \
		--rm -it ${DOCKER_IMAGE_NAME} bash

run: build
	@docker run \
		--rm -it ${DOCKER_IMAGE_NAME}

dc-ps:
	$(DOCKER_COMPOSE_CMD) ps

dc-bash:
	$(DOCKER_COMPOSE_CMD) exec $(filter-out $@,$(MAKECMDGOALS)) bash

dc-run:
	$(DOCKER_COMPOSE_CMD) up --force-recreate --remove-orphans $(filter-out $@,$(MAKECMDGOALS))

dc-build-and-run:
	$(DOCKER_COMPOSE_CMD) up --force-recreate --build

dc-build:
	$(DOCKER_COMPOSE_CMD) build $(filter-out $@,$(MAKECMDGOALS))

%:
	@:
