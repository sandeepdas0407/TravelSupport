from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.schemas import TripPlanRequest, TripPlanResponse
from app.services.trip_planner import build_plan
from app.utils.errors import UpstreamServiceError

router = APIRouter()


SettingsDep = Depends(get_settings)


@router.post("/api/trip-plan", response_model=TripPlanResponse)
async def create_trip_plan(request: TripPlanRequest, settings: Settings = SettingsDep) -> TripPlanResponse:
    try:
        return await build_plan(settings, request)
    except UpstreamServiceError as exc:
        status_code = 400 if exc.service.startswith("azure-maps") else 502
        raise HTTPException(status_code=status_code, detail=f"{exc.service} failed: {exc.message}") from exc
