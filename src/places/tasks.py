from __future__ import annotations

from pathlib import Path

from celery import shared_task
from django.conf import settings

from places.services.swimplace_importer import import_swim_places


@shared_task(name="places.import_swimplaces")
def import_swim_places_task(source_path: str | None = None) -> dict[str, int]:
    resolved_source_path = Path(source_path) if source_path else settings.BASE_DIR / settings.SWIMPLACES_DEFAULT_SOURCE_FILE
    summary = import_swim_places(source_path=resolved_source_path)

    return {
        "created": summary.created,
        "updated": summary.updated,
        "skipped": summary.skipped,
        "processed": summary.processed,
    }
