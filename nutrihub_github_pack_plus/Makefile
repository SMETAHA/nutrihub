SHELL := /bin/bash

.PHONY: run fmt lint fixtures

run: ; python manage.py runserver
migrate: ; python manage.py migrate
fmt: ; ruff check --fix || true ; black . ; isort .
lint: ; ruff check ; black --check . ; isort --check-only .
fixtures: ; python manage.py loaddata fixtures/products.sample.json || true
