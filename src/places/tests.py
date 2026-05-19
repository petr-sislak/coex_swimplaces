import csv
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase, TestCase

from places.models import SwimPlace
from places.services.parsers import merge_descriptions, parse_dog_swimming, parse_swimplace_row
from places.services.swimplace_importer import import_swim_places
from places.tasks import import_swim_places_task


CSV_HEADER = [
    "MapoticID",
    "Longitude",
    "Latitude",
    "Name",
    "Category",
    "Rating",
    "Image URL",
    "Import ID",
    "Description",
    "Address",
    "Web",
    "E-mail",
    "Phone number",
    "Description",
    "Refreshment",
    "Diving",
    "Entrance",
    "Accessibility/parking",
    "Link",
    "Nudist beach",
    "Video",
    "Dog swimming",
]


def build_csv_row(**overrides: str) -> list[str]:
    values = {
        "MapoticID": "202693",
        "Longitude": "14.5424003601",
        "Latitude": "50.2645988464",
        "Name": "Mleklojedy",
        "Category": "Sand quarry",
        "Rating": "3.4782608695652173",
        "Image URL": "https://example.com/image.jpg",
        "Import ID": "swimplaces:1",
        "Description": "",
        "Address": "Test address",
        "Web": "https://example.com",
        "E-mail": "",
        "Phone number": "",
        "Description__detail": "Detailed description",
        "Refreshment": "",
        "Diving": "",
        "Entrance": "",
        "Accessibility/parking": "",
        "Link": "https://example.com/fallback",
        "Nudist beach": "",
        "Video": "",
        "Dog swimming": "Suitable for dogs",
    }
    values.update(overrides)

    return [
        values["MapoticID"],
        values["Longitude"],
        values["Latitude"],
        values["Name"],
        values["Category"],
        values["Rating"],
        values["Image URL"],
        values["Import ID"],
        values["Description"],
        values["Address"],
        values["Web"],
        values["E-mail"],
        values["Phone number"],
        values["Description__detail"],
        values["Refreshment"],
        values["Diving"],
        values["Entrance"],
        values["Accessibility/parking"],
        values["Link"],
        values["Nudist beach"],
        values["Video"],
        values["Dog swimming"],
    ]


class SwimPlaceParserTests(SimpleTestCase):
    def test_parse_swimplace_row_maps_source_columns_to_dto(self) -> None:
        row = parse_swimplace_row(
            build_csv_row(
                Name=" Test place ",
                Description="Short description",
                Description__detail="Detailed description",
                Rating="4.456",
            )
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.external_id, 202693)
        self.assertEqual(row.import_id, "swimplaces:1")
        self.assertEqual(row.name, "Test place")
        self.assertEqual(row.category, "Sand quarry")
        self.assertEqual(row.rating, Decimal("4.46"))
        self.assertEqual(row.latitude, Decimal("50.264599"))
        self.assertEqual(row.longitude, Decimal("14.542400"))
        self.assertEqual(row.description, "Short description\n\nDetailed description")
        self.assertEqual(row.website_url, "https://example.com")
        self.assertIs(row.dog_swimming, True)

    def test_parse_swimplace_row_uses_fallbacks_for_optional_values(self) -> None:
        row = parse_swimplace_row(
            build_csv_row(
                MapoticID="123",
                Category="",
                Rating="",
                **{
                    "Import ID": "",
                    "Web": "",
                    "Dog swimming": "",
                },
            )
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.import_id, "swimplaces:123")
        self.assertEqual(row.category, "Unknown")
        self.assertIsNone(row.rating)
        self.assertEqual(row.website_url, "https://example.com/fallback")
        self.assertIsNone(row.dog_swimming)

    def test_parse_swimplace_row_rejects_invalid_required_values(self) -> None:
        self.assertIsNone(parse_swimplace_row(build_csv_row(MapoticID="")))
        self.assertIsNone(parse_swimplace_row(build_csv_row(Name="")))
        self.assertIsNone(parse_swimplace_row(build_csv_row(Latitude="")))
        self.assertIsNone(parse_swimplace_row(["too", "short"]))

    def test_parse_dog_swimming_maps_known_values(self) -> None:
        self.assertIs(parse_dog_swimming("Suitable for dogs"), True)
        self.assertIs(parse_dog_swimming("Not suitable for dogs"), False)
        self.assertIsNone(parse_dog_swimming(""))

    def test_merge_descriptions_deduplicates_equal_values(self) -> None:
        self.assertEqual(merge_descriptions(" Same text ", "Same text"), "Same text")


class SwimPlaceImporterTests(TestCase):
    def test_import_swim_places_creates_and_updates_places(self) -> None:
        source_path = self.write_csv(
            [
                build_csv_row(MapoticID="1", Name="Original name", **{"Import ID": "swimplaces:1"}),
                build_csv_row(MapoticID="2", Name="Second place", **{"Import ID": "swimplaces:2"}),
            ]
        )

        summary = import_swim_places(source_path)

        self.assertEqual(summary.created, 2)
        self.assertEqual(summary.updated, 0)
        self.assertEqual(summary.skipped, 0)
        self.assertEqual(SwimPlace.objects.count(), 2)

        updated_source_path = self.write_csv(
            [
                build_csv_row(MapoticID="1", Name="Updated name", **{"Import ID": "swimplaces:1"}),
                build_csv_row(MapoticID="2", Name="Second place", **{"Import ID": "swimplaces:2"}),
            ]
        )

        second_summary = import_swim_places(updated_source_path)

        self.assertEqual(second_summary.created, 0)
        self.assertEqual(second_summary.updated, 2)
        self.assertEqual(second_summary.skipped, 0)
        self.assertEqual(SwimPlace.objects.count(), 2)
        self.assertEqual(SwimPlace.objects.get(external_id=1).name, "Updated name")

    def test_import_swim_places_counts_skipped_rows(self) -> None:
        source_path = self.write_csv(
            [
                build_csv_row(MapoticID="1", **{"Import ID": "swimplaces:1"}),
                build_csv_row(MapoticID="", **{"Import ID": "swimplaces:missing"}),
            ]
        )

        summary = import_swim_places(source_path)

        self.assertEqual(summary.created, 1)
        self.assertEqual(summary.updated, 0)
        self.assertEqual(summary.skipped, 1)
        self.assertEqual(SwimPlace.objects.count(), 1)

    def test_import_swim_places_task_imports_source_file(self) -> None:
        source_path = self.write_csv(
            [
                build_csv_row(MapoticID="1", **{"Import ID": "swimplaces:1"}),
                build_csv_row(MapoticID="2", **{"Import ID": "swimplaces:2"}),
            ]
        )

        result = import_swim_places_task.apply(args=(str(source_path),))

        self.assertTrue(result.successful())
        self.assertEqual(
            result.result,
            {
                "created": 2,
                "updated": 0,
                "skipped": 0,
                "processed": 2,
            },
        )
        self.assertEqual(SwimPlace.objects.count(), 2)

    def write_csv(self, rows: list[list[str]]) -> Path:
        temp_file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with temp_file:
            writer = csv.writer(temp_file, delimiter=";")
            writer.writerow(CSV_HEADER)
            writer.writerows(rows)

        return Path(temp_file.name)
