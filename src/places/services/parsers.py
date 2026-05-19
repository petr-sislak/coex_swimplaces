from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from places.services.dto import SwimPlaceImportRow


UNKNOWN_CATEGORY = "Unknown"
RATING_PRECISION = Decimal("0.01")
COORDINATE_PRECISION = Decimal("0.000001")
DEFAULT_HEADER = [
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


def parse_swimplace_row(row: list[str], header: list[str] | None = None) -> SwimPlaceImportRow | None:
    if not row:
        return None

    row_data = build_row_data(header or DEFAULT_HEADER, row)
    external_id = parse_int(get_first(row_data, "MapoticID"))
    name = clean_text(get_first(row_data, "Name"))
    latitude = parse_decimal(get_first(row_data, "Latitude"), precision=COORDINATE_PRECISION)
    longitude = parse_decimal(get_first(row_data, "Longitude"), precision=COORDINATE_PRECISION)

    if external_id is None or not name or latitude is None or longitude is None:
        return None

    return SwimPlaceImportRow(
        external_id=external_id,
        import_id=clean_text(get_first(row_data, "Import ID")) or f"swimplaces:{external_id}",
        name=name,
        category=clean_text(get_first(row_data, "Category")) or UNKNOWN_CATEGORY,
        rating=parse_decimal(get_first(row_data, "Rating"), precision=RATING_PRECISION),
        latitude=latitude,
        longitude=longitude,
        description=merge_descriptions(*get_all(row_data, "Description")),
        image_url=clean_text(get_first(row_data, "Image URL")),
        address=clean_text(get_first(row_data, "Address")),
        website_url=clean_text(get_first(row_data, "Web")) or clean_text(get_first(row_data, "Link")),
        email=clean_text(get_first(row_data, "E-mail")),
        phone_number=clean_text(get_first(row_data, "Phone number")),
        refreshment=clean_text(get_first(row_data, "Refreshment")),
        diving=clean_text(get_first(row_data, "Diving")),
        entrance=clean_text(get_first(row_data, "Entrance")),
        accessibility_parking=clean_text(get_first(row_data, "Accessibility/parking")),
        source_link=clean_text(get_first(row_data, "Link")),
        nudist_beach=clean_text(get_first(row_data, "Nudist beach")),
        video_url=clean_text(get_first(row_data, "Video")),
        dog_swimming=parse_dog_swimming(get_first(row_data, "Dog swimming")),
    )


def build_row_data(header: list[str], row: list[str]) -> dict[str, list[str]]:
    row_data: dict[str, list[str]] = {}
    for index, column_name in enumerate(header):
        normalized_column_name = normalize_column_name(column_name)
        row_data.setdefault(normalized_column_name, []).append(row[index] if index < len(row) else "")
    return row_data


def normalize_column_name(value: str) -> str:
    return clean_text(value).casefold()


def get_first(row_data: dict[str, list[str]], column_name: str) -> str:
    values = get_all(row_data, column_name)
    return values[0] if values else ""


def get_all(row_data: dict[str, list[str]], column_name: str) -> list[str]:
    return row_data.get(normalize_column_name(column_name), [])


def clean_text(value: str) -> str:
    return value.strip()


def merge_descriptions(*descriptions: str) -> str:
    parts = [clean_text(description) for description in descriptions]
    unique_parts = list(dict.fromkeys(part for part in parts if part))
    return "\n\n".join(unique_parts)


def parse_int(value: str) -> int | None:
    try:
        return int(clean_text(value))
    except ValueError:
        return None


def parse_decimal(value: str, precision: Decimal) -> Decimal | None:
    cleaned_value = clean_text(value)
    if not cleaned_value:
        return None

    try:
        return Decimal(cleaned_value).quantize(precision, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None


def parse_dog_swimming(value: str) -> bool | None:
    match clean_text(value):
        case "Suitable for dogs":
            return True
        case "Not suitable for dogs":
            return False
        case _:
            return None
