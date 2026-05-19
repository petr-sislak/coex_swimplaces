# COex Swimplaces

Django aplikace pro testovací task nad exportem koupacích míst.

## Setup

```bash
uv sync
uv run python src/manage.py migrate
uv run python src/manage.py import_swimplaces
```

## Lokální spuštění

```bash
uv run python src/manage.py runserver
```

Frontend je dostupný na `http://127.0.0.1:8000/`.

## Import dat

```bash
uv run python src/manage.py import_swimplaces
```

Importer automaticky detekuje delimiter a mapuje sloupce podle hlavičky. Umí tedy zpracovat původní CSV i update CSV s jiným pořadím sloupců:

```bash
uv run python src/manage.py import_swimplaces --source source_data/swimplaces_export_update.csv
```

Výchozí soubor je řízený přes `SWIMPLACES_DEFAULT_SOURCE_FILE`.

## Celery

Asynchronní import přes Celery task používá stejnou importer service jako management command.

Pro běžný worker je potřeba lokální Redis na URL z `.env`:

```bash
PYTHONPATH=src uv run celery -A config worker -l info
```

Task lze zavolat například z Django shellu:

```bash
uv run python src/manage.py shell
```

```python
from places.tasks import import_swim_places_task

import_swim_places_task.delay()
```

Pro lokální ověření bez workeru lze použít `CELERY_TASK_ALWAYS_EAGER=true`, případně v testech volat `.apply()`.

## Konfigurace

Běžné lokální proměnné jsou v `.env`, citlivé hodnoty jsou simulované v `.secrets/local.env`.
Do Gitu patří pouze `.env.sample` a `.secrets/local.env.sample`.

Důležité proměnné:

- `SWIMPLACES_DEFAULT_SOURCE_FILE`
- `SWIMPLACES_COEX_LATITUDE`
- `SWIMPLACES_COEX_LONGITUDE`
- `SWIMPLACES_STATISTICS_LIMIT`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CELERY_TASK_ALWAYS_EAGER`

## Kontrola projektu

```bash
uv run python src/manage.py check
uv run python src/manage.py test places
```

Zdrojová data vkládat do: `source_data/`.
