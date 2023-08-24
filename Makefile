setup:
	@echo "Setting up Docker, Poetry, and Commitizen environment"
	@if [ ! -f "docker-compose.yml" ]; then \
        echo "  - docker-compose.yml setup..."; \
	    cp docker-compose-default.yml docker-compose.yml; \
    else \
        echo "  - docker-compose.yml file already exists...";\
    fi
	poetry install --with dev
	poetry run pre-commit install --hook-type commit-msg


build:
	poetry update
	docker-compose build

start:
	docker-compose up -d --remove-orphans

status:
	docker-compose ps

stop:
	docker-compose down
