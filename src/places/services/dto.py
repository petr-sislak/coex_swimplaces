from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SwimPlaceImportSummary:
    created: int = 0
    updated: int = 0
    skipped: int = 0

    @property
    def processed(self) -> int:
        return self.created + self.updated


@dataclass(frozen=True)
class SwimPlaceImportRow:
    external_id: int
    import_id: str
    name: str
    category: str
    rating: Decimal | None
    latitude: Decimal
    longitude: Decimal
    description: str
    image_url: str
    address: str
    website_url: str
    dog_swimming: bool | None

    def model_defaults(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "name": self.name,
            "category": self.category,
            "rating": self.rating,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "image_url": self.image_url,
            "address": self.address,
            "website_url": self.website_url,
            "dog_swimming": self.dog_swimming,
        }
