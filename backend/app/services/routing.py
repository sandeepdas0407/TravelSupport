import httpx

from app.config import Settings
from app.schemas import GeoPoint, RouteSummary
from app.utils.errors import UpstreamServiceError

AZURE_MAPS_BASE_URL = "https://atlas.microsoft.com"


async def geocode(client: httpx.AsyncClient, settings: Settings, query: str) -> GeoPoint:
    response = await client.get(
        f"{AZURE_MAPS_BASE_URL}/search/address/json",
        params={
            "api-version": "1.0",
            "subscription-key": settings.azure_maps_subscription_key,
            "query": query,
            "limit": 1,
        },
    )
    if response.status_code != 200:
        raise UpstreamServiceError("azure-maps-geocode", f"status {response.status_code}")

    results = response.json().get("results", [])
    if not results:
        raise UpstreamServiceError("azure-maps-geocode", f"no match for '{query}'")

    top = results[0]
    position = top["position"]
    return GeoPoint(
        query=query,
        lat=position["lat"],
        lon=position["lon"],
        resolved_name=top.get("address", {}).get("freeformAddress", query),
    )


async def get_route(
    client: httpx.AsyncClient, settings: Settings, origin: GeoPoint, destination: GeoPoint
) -> RouteSummary:
    response = await client.get(
        f"{AZURE_MAPS_BASE_URL}/route/directions/json",
        params={
            "api-version": "1.0",
            "subscription-key": settings.azure_maps_subscription_key,
            "query": f"{origin.lat},{origin.lon}:{destination.lat},{destination.lon}",
        },
    )
    if response.status_code != 200:
        raise UpstreamServiceError("azure-maps-route", f"status {response.status_code}")

    routes = response.json().get("routes", [])
    if not routes:
        raise UpstreamServiceError("azure-maps-route", "no route found")

    summary = routes[0]["summary"]
    return RouteSummary(
        origin=origin,
        destination=destination,
        distance_km=summary["lengthInMeters"] / 1000,
        duration_minutes=round(summary["travelTimeInSeconds"] / 60),
    )
