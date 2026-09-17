import httpx
import respx

from app.services import places


@respx.mock
async def test_find_lodging_maps_results(settings, banff) -> None:
    respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
        return_value=httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "place-1",
                        "displayName": {"text": "Banff Park Lodge"},
                        "formattedAddress": "222 Lynx St, Banff, AB",
                        "rating": 4.3,
                        "priceLevel": "PRICE_LEVEL_MODERATE",
                        "googleMapsUri": "https://maps.google.com/?cid=1",
                    }
                ]
            },
        )
    )

    async with httpx.AsyncClient() as client:
        result = await places.find_lodging(client, settings, banff)

    assert len(result) == 1
    assert result[0].name == "Banff Park Lodge"
    assert result[0].google_place_id == "place-1"
