# Makefile

.PHONY: all

build:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart app

rebuild:
	$(MAKE) down
	$(MAKE) build




