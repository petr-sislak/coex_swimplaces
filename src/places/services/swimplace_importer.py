from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from django.db import transaction

from places.models import SwimPlace
from places.services.dto import SwimPlaceImportSummary
from places.services.parsers import parse_swimplace_row


class SwimPlaceImporter:
    def __init__(self, source_path: Path) -> None:
        self.source_path = source_path

    def import_places(self) -> SwimPlaceImportSummary:
        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for raw_row in self._iter_rows():
                row = parse_swimplace_row(raw_row)
                if row is None:
                    skipped += 1
                    continue

                _, was_created = SwimPlace.objects.update_or_create(
                    external_id=row.external_id,
                    defaults=row.model_defaults(),
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return SwimPlaceImportSummary(created=created, updated=updated, skipped=skipped)

    def _iter_rows(self) -> Iterator[list[str]]:
        with self.source_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file, delimiter=";")
            next(reader, None)
            yield from reader


def import_swim_places(source_path: Path) -> SwimPlaceImportSummary:
    return SwimPlaceImporter(source_path=source_path).import_places()
