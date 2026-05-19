from __future__ import annotations

import csv
from pathlib import Path

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
            for header, raw_row in self._iter_rows():
                row = parse_swimplace_row(raw_row, header=header)
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

    def _iter_rows(self):
        with self.source_path.open(encoding="utf-8-sig", newline="") as csv_file:
            sample = csv_file.read(4096)
            csv_file.seek(0)
            dialect = sniff_csv_dialect(sample)
            reader = csv.reader(csv_file, dialect)
            header = next(reader, [])
            expected_columns = len(header)
            pending_row: list[str] | None = None

            for row in reader:
                if not row:
                    continue

                if len(row) < expected_columns and row[0].isdigit():
                    if pending_row is not None:
                        yield header, pending_row
                    pending_row = row
                    continue

                if len(row) < expected_columns and pending_row is not None:
                    pending_row = merge_continuation_row(pending_row, row)
                    if len(pending_row) >= expected_columns:
                        yield header, pending_row[:expected_columns]
                        pending_row = None
                    continue

                if pending_row is not None:
                    yield header, pending_row

                pending_row = row

            if pending_row is not None:
                yield header, pending_row


def merge_continuation_row(row: list[str], continuation: list[str]) -> list[str]:
    if len(row) >= 14:
        row[13] = "\n".join([row[13], continuation[0]]).strip()
        return [*row, *continuation[1:]]

    return [*row, *continuation]


def sniff_csv_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";|,")
    except csv.Error:
        first_line = sample.splitlines()[0] if sample else ""
        delimiter = max([";", "|", ","], key=first_line.count)

        class FallbackDialect(csv.excel):
            pass

        FallbackDialect.delimiter = delimiter
        return FallbackDialect


def import_swim_places(source_path: Path) -> SwimPlaceImportSummary:
    return SwimPlaceImporter(source_path=source_path).import_places()
