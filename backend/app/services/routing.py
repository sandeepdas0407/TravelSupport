import httpx

from app.config import Settings
from app.schemas import GeoPoint, RouteSummary
from app.utils.errors import UpstreamServiceError

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

ROUTES_FIELD_MASK = "routes.distanceMeters,routes.duration"


async def geocode(client: httpx.AsyncClient, settings: Settings, query: str) -> GeoPoint:
    response = await client.get(
        GEOCODE_URL,
        params={"address": query, "key": settings.google_maps_api_key},
    )
    if response.status_code != 200:
        raise UpstreamServiceError("google-maps-geocode", f"status {response.status_code}")

    body = response.json()
    if body.get("status") != "OK":
        raise UpstreamServiceError("google-maps-geocode", body.get("status", "unknown error"))

    results = body.get("results", [])
    if not results:
        raise UpstreamServiceError("google-maps-geocode", f"no match for '{query}'")

    top = results[0]
    location = top["geometry"]["location"]
    return GeoPoint(
        query=query,
        lat=location["lat"],
        lon=location["lng"],
        resolved_name=top.get("formatted_address", query),
    )


async def get_route(
    client: httpx.AsyncClient, settings: Settings, origin: GeoPoint, destination: GeoPoint
) -> RouteSummary:
    response = await client.post(
        ROUTES_URL,
        headers={
            "X-Goog-Api-Key": settings.google_maps_api_key,
            "X-Goog-FieldMask": ROUTES_FIELD_MASK,
            "Content-Type": "application/json",
        },
        json={
            "origin": {"location": {"latLng": {"latitude": origin.lat, "longitude": origin.lon}}},
            "destination": {
                "location": {"latLng": {"latitude": destination.lat, "longitude": destination.lon}}
            },
            "travelMode": "DRIVE",
        },
    )
    if response.status_code != 200:
        raise UpstreamServiceError("google-maps-route", f"status {response.status_code}")

    routes = response.json().get("routes", [])
    if not routes:
        raise UpstreamServiceError("google-maps-route", "no route found")

    top_route = routes[0]
    duration_seconds = int(top_route["duration"].rstrip("s"))
    return RouteSummary(
        origin=origin,
        destination=destination,
        distance_km=top_route["distanceMeters"] / 1000,
        duration_minutes=round(duration_seconds / 60),
    )
