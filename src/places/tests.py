import csv
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

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
CSV_UPDATE_HEADER = [
    "MapoticID",
    "Latitude",
    "Longitude",
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
                **{
                    "E-mail": "info@example.com",
                    "Phone number": "+420 123 456 789",
                    "Refreshment": "Restaurant on site",
                    "Diving": "Suitable for diving",
                    "Entrance": "No entrance fee",
                    "Accessibility/parking": "Very close",
                    "Nudist beach": "Not suitable for nudists",
                    "Video": "https://example.com/video",
                },
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
        self.assertEqual(row.email, "info@example.com")
        self.assertEqual(row.phone_number, "+420 123 456 789")
        self.assertEqual(row.refreshment, "Restaurant on site")
        self.assertEqual(row.diving, "Suitable for diving")
        self.assertEqual(row.entrance, "No entrance fee")
        self.assertEqual(row.accessibility_parking, "Very close")
        self.assertEqual(row.source_link, "https://example.com/fallback")
        self.assertEqual(row.nudist_beach, "Not suitable for nudists")
        self.assertEqual(row.video_url, "https://example.com/video")
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

    def test_parse_swimplace_row_uses_header_mapping_for_reordered_columns(self) -> None:
        row = parse_swimplace_row(
            [
                "202693",
                "50.2645988464",
                "14.5424003601",
                "Mapped place",
                "Sand quarry",
                "3.4782608695652173",
                "https://example.com/image.jpg",
                "swimplaces:1",
                "Short description",
                "Test address",
                "https://example.com",
                "",
                "",
                "Detailed description",
                "",
                "",
                "",
                "",
                "https://example.com/fallback",
                "",
                "",
                "Suitable for dogs",
            ],
            header=CSV_UPDATE_HEADER,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.latitude, Decimal("50.264599"))
        self.assertEqual(row.longitude, Decimal("14.542400"))
        self.assertEqual(row.name, "Mapped place")

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
        self.assertEqual(SwimPlace.objects.get(external_id=1).source_link, "https://example.com/fallback")

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

    def test_import_swim_places_detects_pipe_delimiter_and_header_order(self) -> None:
        source_path = self.write_csv(
            [
                [
                    "1",
                    "50.2645988464",
                    "14.5424003601",
                    "Pipe place",
                    "Sand quarry",
                    "3.4782608695652173",
                    "https://example.com/image.jpg",
                    "swimplaces:1",
                    "",
                    "Test address",
                    "https://example.com",
                    "",
                    "",
                    "Detailed description",
                    "",
                    "",
                    "",
                    "",
                    "https://example.com/fallback",
                    "",
                    "",
                    "Suitable for dogs",
                ],
            ],
            header=CSV_UPDATE_HEADER,
            delimiter="|",
        )

        summary = import_swim_places(source_path)

        self.assertEqual(summary.created, 1)
        place = SwimPlace.objects.get(external_id=1)
        self.assertEqual(place.latitude, Decimal("50.264599"))
        self.assertEqual(place.longitude, Decimal("14.542400"))

    def test_import_swim_places_merges_split_update_rows(self) -> None:
        source_path = self.write_raw_csv(
            "\n".join(
                [
                    "|".join(CSV_UPDATE_HEADER),
                    "1|50.2645988464|14.5424003601|Split place|Sand quarry|3.4782608695652173|"
                    "https://example.com/image.jpg|swimplaces:1||||||First part of description",
                    "second part of description|Restaurant on site|Suitable for diving|No entrance fee|Very close|"
                    "https://example.com/fallback|Not suitable for nudists||Suitable for dogs",
                ]
            )
        )

        summary = import_swim_places(source_path)

        self.assertEqual(summary.created, 1)
        self.assertEqual(summary.skipped, 0)
        place = SwimPlace.objects.get(external_id=1)
        self.assertEqual(place.description, "First part of description\nsecond part of description")
        self.assertEqual(place.refreshment, "Restaurant on site")
        self.assertEqual(place.source_link, "https://example.com/fallback")

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

    def write_csv(self, rows: list[list[str]], header: list[str] | None = None, delimiter: str = ";") -> Path:
        temp_file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with temp_file:
            writer = csv.writer(temp_file, delimiter=delimiter)
            writer.writerow(header or CSV_HEADER)
            writer.writerows(rows)

        return Path(temp_file.name)

    def write_raw_csv(self, content: str) -> Path:
        temp_file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with temp_file:
            temp_file.write(content)

        return Path(temp_file.name)


class PlaceListViewTests(TestCase):
    def test_place_list_renders_import_ids_and_names(self) -> None:
        create_swim_place(external_id=1, import_id="swimplaces:1", name="First place")
        create_swim_place(external_id=2, import_id="swimplaces:2", name="Second place")

        response = self.client.get(reverse("places:place-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "swimplaces:1")
        self.assertContains(response, "First place")
        self.assertContains(response, "swimplaces:2")
        self.assertContains(response, "Second place")

    def test_place_list_links_place_names_to_detail(self) -> None:
        place = create_swim_place(external_id=1, import_id="swimplaces:1", name="Linked place")

        response = self.client.get(reverse("places:place-list"))

        self.assertContains(response, reverse("places:place-detail", args=[place.external_id]))

    def test_place_list_filters_places_suitable_for_dogs(self) -> None:
        create_swim_place(external_id=1, import_id="swimplaces:1", name="Dog place", dog_swimming=True)
        create_swim_place(external_id=2, import_id="swimplaces:2", name="No dog place", dog_swimming=False)

        response = self.client.get(reverse("places:place-list"), {"dog_swimming": "yes"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dog place")
        self.assertNotContains(response, "No dog place")

    def test_place_list_filters_places_not_suitable_for_dogs(self) -> None:
        create_swim_place(external_id=1, import_id="swimplaces:1", name="Dog place", dog_swimming=True)
        create_swim_place(external_id=2, import_id="swimplaces:2", name="No dog place", dog_swimming=False)

        response = self.client.get(reverse("places:place-list"), {"dog_swimming": "no"})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dog place")
        self.assertContains(response, "No dog place")

    def test_place_list_filters_places_with_unknown_dog_swimming(self) -> None:
        create_swim_place(external_id=1, import_id="swimplaces:1", name="Known place", dog_swimming=True)
        create_swim_place(external_id=2, import_id="swimplaces:2", name="Unknown place", dog_swimming=None)

        response = self.client.get(reverse("places:place-list"), {"dog_swimming": "unknown"})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Known place")
        self.assertContains(response, "Unknown place")

    def test_place_list_ignores_invalid_filter_value(self) -> None:
        create_swim_place(external_id=1, import_id="swimplaces:1", name="First place", dog_swimming=True)
        create_swim_place(external_id=2, import_id="swimplaces:2", name="Second place", dog_swimming=False)

        response = self.client.get(reverse("places:place-list"), {"dog_swimming": "invalid"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Filtr nebyl platny")
        self.assertContains(response, "First place")
        self.assertContains(response, "Second place")


class PlaceDetailViewTests(TestCase):
    def test_place_detail_renders_complete_place_data(self) -> None:
        place = create_swim_place(
            external_id=1,
            import_id="swimplaces:1",
            name="Detailed place",
            dog_swimming=True,
        )
        place.description = "Detailed description"
        place.image_url = "https://example.com/image.jpg"
        place.address = "Test address"
        place.website_url = "https://example.com"
        place.email = "info@example.com"
        place.phone_number = "+420 123 456 789"
        place.refreshment = "Restaurant on site"
        place.diving = "Suitable for diving"
        place.entrance = "No entrance fee"
        place.accessibility_parking = "Very close"
        place.source_link = "https://example.com/source"
        place.nudist_beach = "Not suitable for nudists"
        place.video_url = "https://example.com/video"
        place.save()

        response = self.client.get(reverse("places:place-detail", args=[place.external_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detailed place")
        self.assertContains(response, "Detailed description")
        self.assertContains(response, "swimplaces:1")
        self.assertContains(response, "Test address")
        self.assertContains(response, "https://example.com")
        self.assertContains(response, "info@example.com")
        self.assertContains(response, "+420 123 456 789")
        self.assertContains(response, "Restaurant on site")
        self.assertContains(response, "Suitable for diving")
        self.assertContains(response, "No entrance fee")
        self.assertContains(response, "Very close")
        self.assertContains(response, "https://example.com/source")
        self.assertContains(response, "Not suitable for nudists")
        self.assertContains(response, "https://example.com/video")
        self.assertContains(response, "Ano")

    def test_place_detail_returns_404_for_unknown_external_id(self) -> None:
        response = self.client.get(reverse("places:place-detail", args=[999]))

        self.assertEqual(response.status_code, 404)


def create_swim_place(
    *,
    external_id: int,
    import_id: str,
    name: str,
    dog_swimming: bool | None = None,
) -> SwimPlace:
    return SwimPlace.objects.create(
        external_id=external_id,
        import_id=import_id,
        name=name,
        category="Lake",
        rating=Decimal("4.20"),
        latitude=Decimal("50.000000"),
        longitude=Decimal("14.000000"),
        dog_swimming=dog_swimming,
    )
