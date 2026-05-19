from __future__ import annotations

from django.urls import path

from places import views


app_name = "places"

urlpatterns = [
    path("", views.place_list, name="place-list"),
    path("statistics/", views.place_statistics, name="place-statistics"),
    path("places/<int:external_id>/", views.place_detail, name="place-detail"),
]
