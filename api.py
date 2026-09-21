import requests

from config import GEO_URL, FORECAST_URL, log


def geocode(city):
    log.info("Запрос координат для города '%s'", city)
    response = requests.get(
        GEO_URL,
        params={
            "name": city,
            "count": 1,
            "language": "ru",
            "format": "json",
        },
        timeout=10,
    )
    response.raise_for_status()

    results = response.json().get("results")
    if not results:
        raise ValueError(f"Город '{city}' не найден")

    result = results[0]
    return {
        "name": result["name"],
        "country": result.get("country", ""),
        "region": result.get("admin1", ""),
        "lat": result["latitude"],
        "lon": result["longitude"],
    }


def forecast(lat, lon):
    log.info("Запрос прогноза для координат %.2f, %.2f", lat, lon)

    current = (
        "temperature_2m,apparent_temperature,relative_humidity_2m,"
        "wind_speed_10m,precipitation,weather_code"
    )
    daily = (
        "temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,weather_code"
    )

    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": current,
            "daily": daily,
            "timezone": "auto",
            "forecast_days": 3,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()