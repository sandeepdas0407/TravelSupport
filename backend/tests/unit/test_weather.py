from datetime import date, timedelta

import httpx
import respx

from app.services import weather


@respx.mock
async def test_get_weather_for_dates_uses_forecast_within_horizon(settings, banff) -> None:
    today = date.today()
    target = today + timedelta(days=2)

    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(
            200,
            json={
                "daily": {
                    "time": [target.isoformat()],
                    "temperature_2m_min": [4.0],
                    "temperature_2m_max": [14.0],
                    "precipitation_probability_mean": [30],
                    "weathercode": [2],
                }
            },
        )
    )

    async with httpx.AsyncClient() as client:
        result = await weather.get_weather_for_dates(client, settings, banff, [target])

    assert len(result) == 1
    assert result[0].source == "forecast"
    assert result[0].conditions_summary == "Partly cloudy"


@respx.mock
async def test_get_weather_for_dates_uses_climatology_beyond_horizon(settings, banff) -> None:
    today = date.today()
    target = today + timedelta(days=60)

    respx.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=httpx.Response(
            200,
            json={
                "daily": {
                    "temperature_2m_min": [1.0],
                    "temperature_2m_max": [10.0],
                    "precipitation_sum": [0.0],
                }
            },
        )
    )

    async with httpx.AsyncClient() as client:
        result = await weather.get_weather_for_dates(client, settings, banff, [target])

    assert len(result) == 1
    assert result[0].source == "climatology"
    assert result[0].date == target
