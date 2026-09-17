import asyncio
from datetime import UTC, date, datetime

import httpx

from app.config import Settings
from app.schemas import (
    DailyWeather,
    GeoPoint,
    LodgingSuggestion,
    TripPlanMeta,
    TripPlanRequest,
    TripPlanResponse,
)
from app.services import places, routing, synthesis, weather
from app.utils.dates import trip_dates
from app.utils.errors import SynthesisError, UpstreamServiceError

REQUEST_TIMEOUT_SECONDS = 20.0


async def build_plan(settings: Settings, request: TripPlanRequest) -> TripPlanResponse:
    warnings: list[str] = []
    data_sources: list[str] = ["azure-maps-route"]

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        origin, destination = await asyncio.gather(
            routing.geocode(client, settings, request.from_location),
            routing.geocode(client, settings, request.to_location),
        )
        route = await routing.get_route(client, settings, origin, destination)

        dates = trip_dates(request.start_date, request.num_days)

        daily_weather, lodging = await asyncio.gather(
            _weather_with_fallback(client, settings, destination, dates, warnings),
            _lodging_with_fallback(client, settings, destination, warnings),
        )

    if any(day.source == "forecast" for day in daily_weather):
        data_sources.append("open-meteo-forecast")
    if any(day.source == "climatology" for day in daily_weather):
        data_sources.append("open-meteo-archive")
    if lodging:
        data_sources.append("google-places-new")

    try:
        narrative_plan = await synthesis.synthesize_plan(
            settings,
            route,
            daily_weather,
            lodging,
            request.num_days,
            request.start_date,
            request.additional_info,
        )
        data_sources.append("anthropic-messages")
    except SynthesisError as exc:
        raise UpstreamServiceError("anthropic-messages", str(exc)) from exc

    return TripPlanResponse(
        route=route,
        weather=daily_weather,
        lodging=lodging,
        narrative_plan=narrative_plan,
        meta=TripPlanMeta(
            generated_at=datetime.now(UTC),
            model_used=settings.claude_model,
            data_sources_used=data_sources,
            warnings=warnings,
        ),
    )


async def _weather_with_fallback(
    client: httpx.AsyncClient,
    settings: Settings,
    destination: GeoPoint,
    dates: list[date],
    warnings: list[str],
) -> list[DailyWeather]:
    try:
        return await weather.get_weather_for_dates(client, settings, destination, dates)
    except UpstreamServiceError as exc:
        warnings.append(f"Weather data unavailable: {exc.message}")
        return []


async def _lodging_with_fallback(
    client: httpx.AsyncClient, settings: Settings, destination: GeoPoint, warnings: list[str]
) -> list[LodgingSuggestion]:
    try:
        return await places.find_lodging(client, settings, destination)
    except UpstreamServiceError as exc:
        warnings.append(f"Lodging suggestions unavailable: {exc.message}")
        return []
