# makefile
# I decided to use Makefile since it is widespread and does not depend on the technology
# stack being used.
# usage: make <command>
# for example: `make start-compose` executes `docker-compose up -d`

.PHONY: start-compose stop-compose ssh-nginx ssh-django ssh-worker check-network-config-details build-django-app export-env start-db start-dev deploy
start-compose:
	@echo '--- Starting the updated app in the background...'
#@export CURRENT_UID=$(id -u):$(id -g);
	docker-compose up -d

stop-compose:
	@echo '--- Stopping the app...'
	@docker-compose down

ssh-nginx:
	@docker exec -it web bash

ssh-django:
	@docker exec -it app bash

ssh-worker:
	@docker exec -it worker bash

check-network-config-details:
	@docker network inspect tumar

build-django-app:
	@echo '--- Building the app with the new updates...'
	@docker build -t tumar/app:latest .

export-env:
	@echo '--- Exporting all installed packages to environment.yml file...'
	conda env export --no-builds --name tumar_dev > environment.yml

start-db:
	@echo '--- Turning on postgres database in the conda development environment...'
	pg_ctl -D base_db -l logfile start

start-dev:
	@echo '--- Turning on postgres database in the conda development environment...'
	@python manage.py migrate
	@echo '--- Collecting static files (js, html, css, etc)...'
	@python ./manage.py collectstatic --noinput
	@echo '--- Compiling translations (primarily for Russian language)...'
	@python ./manage.py compilemessages
	@python manage.py runserver 0.0.0.0:8000

pull:
	@echo '--- Pulling the app updates from the repository...'
	@git pull

deploy: stop-compose build-django-app start-compose
