from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


DogSwimmingFilter = Literal["all", "yes", "no", "unknown"]


class PlaceListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dog_swimming: DogSwimmingFilter = "all"
