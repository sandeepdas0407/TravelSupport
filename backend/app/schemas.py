from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TripPlanRequest(BaseModel):
    from_location: str = Field(min_length=2, max_length=200)
    to_location: str = Field(min_length=2, max_length=200)
    start_date: date
    num_days: int = Field(ge=1, le=21)
    additional_info: str | None = Field(default=None, max_length=2000)

    @field_validator("start_date")
    @classmethod
    def start_date_not_in_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("start_date cannot be in the past")
        return value


class GeoPoint(BaseModel):
    query: str
    lat: float
    lon: float
    resolved_name: str


class RouteSummary(BaseModel):
    origin: GeoPoint
    destination: GeoPoint
    distance_km: float
    duration_minutes: int


WeatherSource = Literal["forecast", "climatology"]


class DailyWeather(BaseModel):
    date: date
    source: WeatherSource
    temp_min_c: float
    temp_max_c: float
    precip_probability_pct: float
    conditions_summary: str


class LodgingSuggestion(BaseModel):
    name: str
    address: str
    rating: float | None
    price_level: str | None
    google_place_id: str
    maps_url: str


class DayPlan(BaseModel):
    day_number: int
    date: date
    title: str
    description: str


class NarrativePlan(BaseModel):
    summary: str
    day_by_day: list[DayPlan]
    recommended_stays: list[str]
    packing_suggestions: list[str]


class TripPlanMeta(BaseModel):
    generated_at: datetime
    model_used: str
    data_sources_used: list[str]
    warnings: list[str] = Field(default_factory=list)


class TripPlanResponse(BaseModel):
    route: RouteSummary
    weather: list[DailyWeather]
    lodging: list[LodgingSuggestion]
    narrative_plan: NarrativePlan
    meta: TripPlanMeta
