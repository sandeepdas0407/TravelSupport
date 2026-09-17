from datetime import date, timedelta

from app.utils.dates import is_within_forecast_horizon, season_for, trip_dates


def test_trip_dates_generates_consecutive_days() -> None:
    start = date(2026, 10, 5)
    assert trip_dates(start, 3) == [date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7)]


def test_is_within_forecast_horizon_true_for_near_dates() -> None:
    today = date(2026, 9, 17)
    assert is_within_forecast_horizon(today + timedelta(days=10), today) is True


def test_is_within_forecast_horizon_false_for_far_dates() -> None:
    today = date(2026, 9, 17)
    assert is_within_forecast_horizon(today + timedelta(days=30), today) is False


def test_is_within_forecast_horizon_boundary() -> None:
    # Open-Meteo's forecast API rejects a date more than 15 days out from today
    # (today+16 returns a 400): the boundary must sit at exactly 15, not 16.
    today = date(2026, 9, 17)
    assert is_within_forecast_horizon(today + timedelta(days=15), today) is True
    assert is_within_forecast_horizon(today + timedelta(days=16), today) is False


def test_season_for_northern_hemisphere() -> None:
    assert season_for(date(2026, 1, 15)) == "winter"
    assert season_for(date(2026, 7, 15)) == "summer"


def test_season_for_southern_hemisphere() -> None:
    assert season_for(date(2026, 1, 15), hemisphere_is_northern=False) == "summer"
