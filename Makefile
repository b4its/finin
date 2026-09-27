# ==============================================================
# Financial Twin — Makefile
# Pakai: make <target>      Lihat semua: make help
# Target per-service: tambahkan s=<service>, contoh: make logs s=backend
# ==============================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

-include .env
export

COMPOSE    ?= docker compose
BE         := backend
FE         := frontend
DB         := db
BACKUP_DIR := backups
TS         := $(shell date +%Y%m%d_%H%M%S)

.PHONY: help init env up dev down stop start restart build rebuild ps logs \
	logs-be logs-fe logs-db sh-be sh-fe psql migrate migration downgrade \
	db-history seed seed-demo test test-be test-fe e2e bench lint format \
	typecheck check tools tools-down db-backup db-restore db-reset health \
	urls clean prune

## ---------- Bantuan ----------
help: ## Tampilkan daftar perintah
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

## ---------- Setup ----------
env: ## Buat .env dari .env.example (jika belum ada)
	@test -f .env && echo ".env sudah ada" || (cp .env.example .env && echo ".env dibuat")

init: env ## Setup pertama: .env, build, up, migrate, seed
	@$(MAKE) --no-print-directory build
	@$(MAKE) --no-print-directory up
	@$(MAKE) --no-print-directory migrate
	@$(MAKE) --no-print-directory seed

## ---------- Lifecycle ----------
up: ## Jalankan semua layanan (background)
	$(COMPOSE) up -d $(s)
	@$(MAKE) --no-print-directory urls

dev: ## Jalankan foreground + log langsung
	$(COMPOSE) up $(s)

down: ## Hentikan & hapus container (data DB tetap aman)
	$(COMPOSE) down

stop: ## Hentikan container tanpa menghapus
	$(COMPOSE) stop $(s)

start: ## Nyalakan kembali container yang di-stop
	$(COMPOSE) start $(s)

restart: ## Restart semua / satu layanan (s=backend)
	$(COMPOSE) restart $(s)

build: ## Build image (s=backend untuk satu layanan)
	$(COMPOSE) build $(s)

rebuild: ## Build ulang tanpa cache lalu jalankan
	$(COMPOSE) build --no-cache $(s)
	$(COMPOSE) up -d $(s)

ps: ## Status container
	$(COMPOSE) ps

## ---------- Log & Shell ----------
logs: ## Log semua / satu layanan (s=backend)
	$(COMPOSE) logs -f --tail=200 $(s)

logs-be: ## Log backend
	$(COMPOSE) logs -f --tail=200 $(BE)

logs-fe: ## Log frontend
	$(COMPOSE) logs -f --tail=200 $(FE)

logs-db: ## Log database
	$(COMPOSE) logs -f --tail=200 $(DB)

sh-be: ## Masuk shell backend
	$(COMPOSE) exec $(BE) bash

sh-fe: ## Masuk shell frontend
	$(COMPOSE) exec $(FE) sh

psql: ## Masuk psql
	$(COMPOSE) exec $(DB) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

## ---------- Database ----------
migrate: ## Jalankan migrasi Alembic ke head
	$(COMPOSE) exec $(BE) alembic upgrade head

migration: ## Buat migrasi baru: make migration m="pesan"
	@test -n "$(m)" || (echo 'Pakai: make migration m="pesan"'; exit 1)
	$(COMPOSE) exec $(BE) alembic revision --autogenerate -m "$(m)"

downgrade: ## Mundur 1 migrasi
	$(COMPOSE) exec $(BE) alembic downgrade -1

db-history: ## Riwayat migrasi
	$(COMPOSE) exec $(BE) alembic history --verbose

seed: ## Seed set asumsi default (ASSUMPTION_SET)
	$(COMPOSE) exec $(BE) python -m app.scripts.seed_assumptions

seed-demo: ## Seed persona demo + pre-cache narasi
	$(COMPOSE) exec $(BE) python -m app.scripts.seed_demo

db-backup: ## Backup DB ke folder backups/
	@mkdir -p $(BACKUP_DIR)
	$(COMPOSE) exec -T $(DB) pg_dump -U $(POSTGRES_USER) -d $(POSTGRES_DB) > $(BACKUP_DIR)/$(POSTGRES_DB)_$(TS).sql
	@echo "Backup tersimpan: $(BACKUP_DIR)/$(POSTGRES_DB)_$(TS).sql"

db-restore: ## Restore DB: make db-restore f=backups/file.sql
	@test -f "$(f)" || (echo 'Pakai: make db-restore f=backups/file.sql'; exit 1)
	$(COMPOSE) exec -T $(DB) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < $(f)

db-reset: ## HAPUS semua data DB lalu migrate + seed ulang
	@read -p "Yakin hapus semua data DB? [y/N] " a; [ "$$a" = "y" ] || exit 1
	$(COMPOSE) down -v
	$(COMPOSE) up -d --wait $(DB) $(BE)
	@$(MAKE) --no-print-directory migrate
	@$(MAKE) --no-print-directory seed

## ---------- Kualitas ----------
test: test-be test-fe ## Semua unit test

test-be: ## Test backend + coverage
	$(COMPOSE) exec -e TEST_DATABASE_URL=postgresql+asyncpg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(DB):5432/$(POSTGRES_DB) $(BE) pytest -q --cov=app --cov-report=term

test-fe: ## Test frontend (vitest)
	$(COMPOSE) exec $(FE) npm run test -- --run

e2e: ## E2E Playwright (dijalankan di host)
	cd frontend && npx playwright test

bench: ## Benchmark engine (target < 300 ms)
	$(COMPOSE) exec $(BE) python -m app.scripts.bench_engine

lint: ## Lint backend + frontend
	$(COMPOSE) exec $(BE) ruff check app
	$(COMPOSE) exec $(FE) npm run lint

format: ## Format kode
	$(COMPOSE) exec $(BE) ruff format app
	$(COMPOSE) exec $(FE) npm run format

typecheck: ## Cek tipe (mypy + svelte-check)
	$(COMPOSE) exec $(BE) mypy app
	$(COMPOSE) exec $(FE) npm run check

check: lint typecheck test ## Lint + typecheck + test (sebelum commit)

## ---------- Tools & Utilitas ----------
tools: ## Jalankan pgAdmin
	$(COMPOSE) --profile tools up -d pgadmin
	@echo "pgAdmin: http://localhost:$(PGADMIN_PORT)"

tools-down: ## Matikan pgAdmin
	$(COMPOSE) --profile tools stop pgadmin

health: ## Cek kesehatan semua layanan
	@curl -fsS http://localhost:$(BACKEND_PORT)/api/v1/health >/dev/null && echo "backend  : OK" || echo "backend  : GAGAL"
	@curl -fsS -o /dev/null http://localhost:$(FRONTEND_PORT) && echo "frontend : OK" || echo "frontend : GAGAL"
	@$(COMPOSE) exec -T $(DB) pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB) >/dev/null && echo "database : OK" || echo "database : GAGAL"

urls: ## Tampilkan URL layanan
	@echo "Frontend : http://localhost:$(FRONTEND_PORT)"
	@echo "API docs : http://localhost:$(BACKEND_PORT)/docs"
	@echo "Postgres : localhost:$(POSTGRES_PORT)"
	@echo "pgAdmin  : http://localhost:$(PGADMIN_PORT)  (make tools)"

clean: ## Hapus container + volume (DATA HILANG)
	@read -p "Hapus container & volume? [y/N] " a; [ "$$a" = "y" ] || exit 1
	$(COMPOSE) down -v --remove-orphans

prune: ## Bersihkan image/cache Docker tak terpakai
	docker system prune -f
