# COex Swimplaces

Django aplikace pro testovací task nad exportem koupacích míst.

## Lokální spuštění

```bash
uv sync
uv run python src/manage.py migrate
uv run python src/manage.py runserver
```

## Import dat

```bash
uv run python src/manage.py import_swimplaces
```

Asynchronní import přes Celery task používá stejnou importer service.
Pro běžný worker je potřeba lokální Redis na URL z `.env`.

```bash
PYTHONPATH=src uv run celery -A config worker -l info
```

Pro lokální ověření bez workeru lze dočasně nastavit `CELERY_TASK_ALWAYS_EAGER=true`.

## Konfigurace

Běžné lokální proměnné jsou v `.env`, citlivé hodnoty jsou simulované v `.secrets/local.env`.
Do Gitu patří pouze `.env.sample` a `.secrets/local.env.sample`.

## Kontrola projektu

```bash
uv run python src/manage.py check
```

Zdrojová data jsou v `source_data/swimplaces_export.csv`.
