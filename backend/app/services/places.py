import httpx

from app.config import Settings
from app.schemas import GeoPoint, LodgingSuggestion
from app.utils.errors import UpstreamServiceError

PLACES_SEARCH_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
SEARCH_RADIUS_METERS = 15_000
MAX_RESULTS = 6

FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.rating",
        "places.priceLevel",
        "places.googleMapsUri",
    ]
)


async def find_lodging(
    client: httpx.AsyncClient, settings: Settings, destination: GeoPoint
) -> list[LodgingSuggestion]:
    response = await client.post(
        PLACES_SEARCH_NEARBY_URL,
        headers={
            "X-Goog-Api-Key": settings.google_places_api_key,
            "X-Goog-FieldMask": FIELD_MASK,
            "Content-Type": "application/json",
        },
        json={
            "includedTypes": ["lodging"],
            "maxResultCount": MAX_RESULTS,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": destination.lat, "longitude": destination.lon},
                    "radius": SEARCH_RADIUS_METERS,
                }
            },
        },
    )
    if response.status_code != 200:
        raise UpstreamServiceError("google-places", f"status {response.status_code}")

    places = response.json().get("places", [])
    return [
        LodgingSuggestion(
            name=place.get("displayName", {}).get("text", "Unknown lodging"),
            address=place.get("formattedAddress", ""),
            rating=place.get("rating"),
            price_level=place.get("priceLevel"),
            google_place_id=place["id"],
            maps_url=place.get("googleMapsUri", f"https://www.google.com/maps/place/?q=place_id:{place['id']}"),
        )
        for place in places
    ]
