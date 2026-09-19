import requests

from config import log, GEO_URL, FORECAST_URL


def geocode(city):
    log.info("Запрос координат для города '%s'", city)
    resp = requests.get(GEO_URL, params={
        "name": city,
        "count": 1,
        "language": "ru",
        "format": "json",
    }, timeout=10)
    resp.raise_for_status()

    results = resp.json().get("results")
    if not results:
        raise ValueError(f"Город '{city}' не найден")

    r = results[0]
    return {
        "name": r["name"],
        "country": r.get("country", ""),
        "lat": r["latitude"],
        "lon": r["longitude"],
    }


def forecast(lat, lon):
    log.info("Запрос прогноза для координат %.2f, %.2f", lat, lon)

    current = "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,precipitation,weather_code"
    daily = "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"

    resp = requests.get(FORECAST_URL, params={
        "latitude": lat,
        "longitude": lon,
        "current": current,
        "daily": daily,
        "timezone": "auto",
        "forecast_days": 3,
    }, timeout=10)
    resp.raise_for_status()
    return resp.json()