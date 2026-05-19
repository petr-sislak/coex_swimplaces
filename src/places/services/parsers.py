from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from places.services.dto import SwimPlaceImportRow


UNKNOWN_CATEGORY = "Unknown"
RATING_PRECISION = Decimal("0.01")
COORDINATE_PRECISION = Decimal("0.000001")


def parse_swimplace_row(row: list[str]) -> SwimPlaceImportRow | None:
    if len(row) < 22:
        return None

    external_id = parse_int(row[0])
    name = clean_text(row[3])
    latitude = parse_decimal(row[2], precision=COORDINATE_PRECISION)
    longitude = parse_decimal(row[1], precision=COORDINATE_PRECISION)

    if external_id is None or not name or latitude is None or longitude is None:
        return None

    return SwimPlaceImportRow(
        external_id=external_id,
        import_id=clean_text(row[7]) or f"swimplaces:{external_id}",
        name=name,
        category=clean_text(row[4]) or UNKNOWN_CATEGORY,
        rating=parse_decimal(row[5], precision=RATING_PRECISION),
        latitude=latitude,
        longitude=longitude,
        description=merge_descriptions(short_description=row[8], description=row[13]),
        image_url=clean_text(row[6]),
        address=clean_text(row[9]),
        website_url=clean_text(row[10]) or clean_text(row[18]),
        email=clean_text(row[11]),
        phone_number=clean_text(row[12]),
        refreshment=clean_text(row[14]),
        diving=clean_text(row[15]),
        entrance=clean_text(row[16]),
        accessibility_parking=clean_text(row[17]),
        source_link=clean_text(row[18]),
        nudist_beach=clean_text(row[19]),
        video_url=clean_text(row[20]),
        dog_swimming=parse_dog_swimming(row[21]),
    )


def clean_text(value: str) -> str:
    return value.strip()


def merge_descriptions(short_description: str, description: str) -> str:
    parts = [clean_text(short_description), clean_text(description)]
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
