import asyncio
from datetime import date

import httpx

from app.config import Settings
from app.schemas import DailyWeather, GeoPoint
from app.utils.dates import is_within_forecast_horizon
from app.utils.errors import UpstreamServiceError

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
CLIMATOLOGY_LOOKBACK_YEARS = 5

_WEATHER_CODE_SUMMARY: dict[int, str] = {
    0: "Clear sky",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def _summarize_code(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return _WEATHER_CODE_SUMMARY.get(code, "Mixed conditions")


def _safe_replace_year(target_date: date, year: int) -> date | None:
    try:
        return target_date.replace(year=year)
    except ValueError:
        # Feb 29 has no equivalent in a non-leap year; skip that sample.
        return None


async def get_weather_for_dates(
    client: httpx.AsyncClient, settings: Settings, destination: GeoPoint, dates: list[date]
) -> list[DailyWeather]:
    today = date.today()
    forecast_dates = sorted(d for d in dates if is_within_forecast_horizon(d, today))
    climatology_dates = sorted(d for d in dates if d not in forecast_dates)

    results: list[DailyWeather] = []
    if forecast_dates:
        results.extend(await _fetch_forecast(client, destination, forecast_dates))
    if climatology_dates:
        climatology_results = await asyncio.gather(
            *(_fetch_climatology_for_date(client, destination, d) for d in climatology_dates)
        )
        results.extend(climatology_results)

    return sorted(results, key=lambda day: day.date)


async def _fetch_forecast(
    client: httpx.AsyncClient, destination: GeoPoint, dates: list[date]
) -> list[DailyWeather]:
    response = await client.get(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": destination.lat,
            "longitude": destination.lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_mean,weathercode",
            "timezone": "auto",
            "start_date": dates[0].isoformat(),
            "end_date": dates[-1].isoformat(),
        },
    )
    if response.status_code != 200:
        raise UpstreamServiceError("open-meteo-forecast", f"status {response.status_code}")

    daily = response.json().get("daily", {})
    wanted = {d.isoformat() for d in dates}

    precip_by_index = daily.get("precipitation_probability_mean", [0] * len(daily["time"]))
    weathercode_by_index = daily.get("weathercode", [None] * len(daily["time"]))

    out: list[DailyWeather] = []
    for i, day_str in enumerate(daily.get("time", [])):
        if day_str not in wanted:
            continue
        out.append(
            DailyWeather(
                date=day_str,
                source="forecast",
                temp_min_c=daily["temperature_2m_min"][i],
                temp_max_c=daily["temperature_2m_max"][i],
                precip_probability_pct=precip_by_index[i] or 0,
                conditions_summary=_summarize_code(weathercode_by_index[i]),
            )
        )
    return out


async def _fetch_climatology_for_date(
    client: httpx.AsyncClient, destination: GeoPoint, target_date: date
) -> DailyWeather:
    current_year = date.today().year
    past_years = [current_year - offset for offset in range(1, CLIMATOLOGY_LOOKBACK_YEARS + 1)]
    historical_dates = [d for year in past_years if (d := _safe_replace_year(target_date, year)) is not None]

    responses = await asyncio.gather(
        *(_fetch_archive_day(client, destination, historical_date) for historical_date in historical_dates),
        return_exceptions=True,
    )
    samples = [r for r in responses if isinstance(r, tuple)]

    if not samples:
        raise UpstreamServiceError("open-meteo-archive", f"no historical data for {target_date.isoformat()}")

    temp_mins = [s[0] for s in samples]
    temp_maxs = [s[1] for s in samples]
    precip_days = [s[2] for s in samples]

    return DailyWeather(
        date=target_date,
        source="climatology",
        temp_min_c=sum(temp_mins) / len(temp_mins),
        temp_max_c=sum(temp_maxs) / len(temp_maxs),
        precip_probability_pct=round(100 * sum(precip_days) / len(precip_days)),
        conditions_summary=f"Historical average ({len(samples)}yr)",
    )


async def _fetch_archive_day(
    client: httpx.AsyncClient, destination: GeoPoint, historical_date: date
) -> tuple[float, float, bool]:
    response = await client.get(
        OPEN_METEO_ARCHIVE_URL,
        params={
            "latitude": destination.lat,
            "longitude": destination.lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "start_date": historical_date.isoformat(),
            "end_date": historical_date.isoformat(),
        },
    )
    response.raise_for_status()
    daily = response.json()["daily"]
    temp_min = daily["temperature_2m_min"][0]
    temp_max = daily["temperature_2m_max"][0]
    precip = daily["precipitation_sum"][0] or 0
    return temp_min, temp_max, precip > 1.0
