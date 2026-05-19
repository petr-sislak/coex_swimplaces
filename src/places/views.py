from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from pydantic import ValidationError

from places.models import SwimPlace
from places.schemas import PlaceListQuery


def place_list(request: HttpRequest) -> HttpResponse:
    query, query_errors = parse_place_list_query(request)
    places = apply_place_list_filters(SwimPlace.objects.all(), query)

    context = {
        "places": places,
        "query": query,
        "query_errors": query_errors,
        "dog_swimming_options": [
            ("all", "Vse"),
            ("yes", "Ano"),
            ("no", "Ne"),
            ("unknown", "Bez informace"),
        ],
    }
    return render(request, "places/place_list.html", context)


def parse_place_list_query(request: HttpRequest) -> tuple[PlaceListQuery, list[str]]:
    raw_query: dict[str, Any] = {}
    if "dog_swimming" in request.GET:
        raw_query["dog_swimming"] = request.GET["dog_swimming"]

    try:
        return PlaceListQuery.model_validate(raw_query), []
    except ValidationError as exc:
        return PlaceListQuery(), [error["msg"] for error in exc.errors()]


def apply_place_list_filters(queryset: QuerySet[SwimPlace], query: PlaceListQuery) -> QuerySet[SwimPlace]:
    match query.dog_swimming:
        case "yes":
            return queryset.filter(dog_swimming=True)
        case "no":
            return queryset.filter(dog_swimming=False)
        case "unknown":
            return queryset.filter(dog_swimming__isnull=True)
        case _:
            return queryset
