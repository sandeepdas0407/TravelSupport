import pytest

from app.config import Settings
from app.schemas import GeoPoint


@pytest.fixture
def settings() -> Settings:
    return Settings(
        anthropic_api_key="test-anthropic-key",
        google_maps_api_key="test-google-maps-key",
        google_places_api_key="test-google-places-key",
    )


@pytest.fixture
def banff() -> GeoPoint:
    return GeoPoint(query="Banff, AB", lat=51.1784, lon=-115.5708, resolved_name="Banff, AB, Canada")
