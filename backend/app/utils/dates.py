from datetime import date, timedelta

# Open-Meteo's forecast API rejects a start/end date more than 15 days out from today
# (empirically verified: today+15 succeeds, today+16 returns 400 "out of allowed range").
FORECAST_HORIZON_DAYS = 15


def trip_dates(start_date: date, num_days: int) -> list[date]:
    return [start_date + timedelta(days=offset) for offset in range(num_days)]


def is_within_forecast_horizon(target_date: date, today: date | None = None) -> bool:
    reference = today or date.today()
    return (target_date - reference).days <= FORECAST_HORIZON_DAYS


def season_for(target_date: date, hemisphere_is_northern: bool = True) -> str:
    month = target_date.month
    if hemisphere_is_northern:
        seasons = {
            (12, 1, 2): "winter",
            (3, 4, 5): "spring",
            (6, 7, 8): "summer",
            (9, 10, 11): "autumn",
        }
    else:
        seasons = {
            (12, 1, 2): "summer",
            (3, 4, 5): "autumn",
            (6, 7, 8): "winter",
            (9, 10, 11): "spring",
        }
    for months, season in seasons.items():
        if month in months:
            return season
    raise ValueError(f"Unreachable: month {month} not in any season")
