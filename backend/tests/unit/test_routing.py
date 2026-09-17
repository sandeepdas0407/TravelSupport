import httpx
import pytest
import respx

from app.services import routing
from app.utils.errors import UpstreamServiceError


@respx.mock
async def test_geocode_returns_geo_point(settings) -> None:
    respx.get("https://atlas.microsoft.com/search/address/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "position": {"lat": 51.1784, "lon": -115.5708},
                        "address": {"freeformAddress": "Banff, AB, Canada"},
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        point = await routing.geocode(client, settings, "Banff, AB")

    assert point.lat == 51.1784
    assert point.resolved_name == "Banff, AB, Canada"


@respx.mock
async def test_geocode_raises_on_no_results(settings) -> None:
    respx.get("https://atlas.microsoft.com/search/address/json").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(UpstreamServiceError):
            await routing.geocode(client, settings, "Nowhereville")


@respx.mock
async def test_get_route_returns_summary(settings, banff) -> None:
    origin = banff.model_copy(update={"lat": 47.6, "lon": -122.33, "resolved_name": "Seattle, WA"})
    respx.get("https://atlas.microsoft.com/route/directions/json").mock(
        return_value=httpx.Response(
            200,
            json={"routes": [{"summary": {"lengthInMeters": 970_000, "travelTimeInSeconds": 37_200}}]},
        )
    )
    async with httpx.AsyncClient() as client:
        route = await routing.get_route(client, settings, origin, banff)

    assert route.distance_km == pytest.approx(970.0)
    assert route.duration_minutes == 620
