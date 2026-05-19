from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.conf import settings
from django.db.models import Count

from places.models import SwimPlace


EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class CategoryCount:
    category: str
    count: int


@dataclass(frozen=True)
class DistantPlace:
    place: SwimPlace
    distance_km: float


@dataclass(frozen=True)
class SwimPlaceStatistics:
    total_count: int
    limit: int
    category_counts: list[CategoryCount]
    top_rated_places: list[SwimPlace]
    most_distant_places: list[DistantPlace]


def get_swim_place_statistics() -> SwimPlaceStatistics:
    places = SwimPlace.objects.all()
    limit = settings.SWIMPLACES_STATISTICS_LIMIT
    return SwimPlaceStatistics(
        total_count=places.count(),
        limit=limit,
        category_counts=get_category_counts(),
        top_rated_places=list(places.exclude(rating__isnull=True).order_by("-rating", "name")[:limit]),
        most_distant_places=get_most_distant_places(limit=limit),
    )


def get_category_counts() -> list[CategoryCount]:
    rows = (
        SwimPlace.objects.values("category")
        .annotate(count=Count("id"))
        .order_by("-count", "category")
    )
    return [CategoryCount(category=row["category"], count=row["count"]) for row in rows]


def get_most_distant_places(limit: int) -> list[DistantPlace]:
    distant_places = [
        DistantPlace(
            place=place,
            distance_km=calculate_distance_km(
                float(place.latitude),
                float(place.longitude),
                float(Decimal(settings.SWIMPLACES_COEX_LATITUDE)),
                float(Decimal(settings.SWIMPLACES_COEX_LONGITUDE)),
            ),
        )
        for place in SwimPlace.objects.all()
    ]
    return sorted(distant_places, key=lambda item: item.distance_km, reverse=True)[:limit]


def calculate_distance_km(
    latitude: float,
    longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    latitude_radians = radians(latitude)
    longitude_radians = radians(longitude)
    target_latitude_radians = radians(target_latitude)
    target_longitude_radians = radians(target_longitude)

    latitude_delta = target_latitude_radians - latitude_radians
    longitude_delta = target_longitude_radians - longitude_radians

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(latitude_radians) * cos(target_latitude_radians) * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(haversine))
