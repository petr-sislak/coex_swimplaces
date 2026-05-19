from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from places.services.swimplace_importer import import_swim_places


class Command(BaseCommand):
    help = "Import swim places from a Mapotic CSV export."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source",
            type=Path,
            default=settings.BASE_DIR / settings.SWIMPLACES_DEFAULT_SOURCE_FILE,
            help="Path to the source CSV file.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source_path = options["source"]

        if not source_path.exists():
            self.stderr.write(self.style.ERROR(f"Source file does not exist: {source_path}"))
            return

        summary = import_swim_places(source_path=source_path)
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported swim places: created={summary.created}, "
                f"updated={summary.updated}, skipped={summary.skipped}"
            )
        )
