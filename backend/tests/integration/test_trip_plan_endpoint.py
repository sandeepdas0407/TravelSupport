from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.routers import trip_plan as trip_plan_router
from app.schemas import (
    DayPlan,
    GeoPoint,
    NarrativePlan,
    RouteSummary,
    TripPlanMeta,
    TripPlanResponse,
)
from app.utils.errors import UpstreamServiceError

client = TestClient(app)


def _sample_response() -> TripPlanResponse:
    origin = GeoPoint(query="Seattle, WA", lat=47.6, lon=-122.33, resolved_name="Seattle, WA, USA")
    destination = GeoPoint(query="Banff, AB", lat=51.18, lon=-115.57, resolved_name="Banff, AB, Canada")
    return TripPlanResponse(
        route=RouteSummary(origin=origin, destination=destination, distance_km=970, duration_minutes=620),
        weather=[],
        lodging=[],
        narrative_plan=NarrativePlan(
            summary="A scenic drive.",
            day_by_day=[DayPlan(day_number=1, date=date.today(), title="Day 1", description="Drive.")],
            recommended_stays=[],
            packing_suggestions=[],
        ),
        meta=TripPlanMeta(
            generated_at=datetime.now(UTC),
            model_used="claude-sonnet-4-5",
            data_sources_used=["azure-maps-route"],
            warnings=[],
        ),
    )


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_trip_plan_returns_plan(monkeypatch) -> None:
    async def fake_build_plan(settings, request):
        return _sample_response()

    monkeypatch.setattr(trip_plan_router, "build_plan", fake_build_plan)

    response = client.post(
        "/api/trip-plan",
        json={
            "from_location": "Seattle, WA",
            "to_location": "Banff, AB",
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "num_days": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route"]["destination"]["resolved_name"] == "Banff, AB, Canada"


def test_trip_plan_rejects_past_date() -> None:
    response = client.post(
        "/api/trip-plan",
        json={
            "from_location": "Seattle, WA",
            "to_location": "Banff, AB",
            "start_date": (date.today() - timedelta(days=1)).isoformat(),
            "num_days": 3,
        },
    )
    assert response.status_code == 422


def test_trip_plan_maps_geocode_failure_to_400(monkeypatch) -> None:
    async def fake_build_plan(settings, request):
        raise UpstreamServiceError("azure-maps-geocode", "no match")

    monkeypatch.setattr(trip_plan_router, "build_plan", fake_build_plan)

    response = client.post(
        "/api/trip-plan",
        json={
            "from_location": "Nowhereville",
            "to_location": "Banff, AB",
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "num_days": 3,
        },
    )
    assert response.status_code == 400
