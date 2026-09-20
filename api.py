import requests

from config import log, GEO_URL, FORECAST_URL


def geocode(city):
    log.info("Поиск координат города: %s", city)

    params = {
        "name": city,
        "count": 1,
        "language": "ru",
        "format": "json",
    }

    try:
        response = requests.get(
            GEO_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException:
        log.exception("Ошибка при поиске координат города")
        raise

    results = response.json().get("results")

    if not results:
        log.warning("Город не найден: %s", city)
        raise ValueError(f"Город '{city}' не найден")

    result = results[0]

    geo = {
        "name": result["name"],
        "country": result.get("country", ""),
        "lat": result["latitude"],
        "lon": result["longitude"],
    }

    log.info(
        "Координаты получены: %s, %s",
        geo["name"],
        geo["country"]
    )

    return geo


def forecast(lat, lon):
    log.info(
        "Запрос прогноза для координат %.4f, %.4f",
        lat,
        lon
    )

    current = (
        "temperature_2m,"
        "apparent_temperature,"
        "relative_humidity_2m,"
        "wind_speed_10m,"
        "precipitation,"
        "weather_code"
    )

    daily = (
        "temperature_2m_max,"
        "temperature_2m_min,"
        "precipitation_probability_max,"
        "weather_code"
    )

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": current,
        "daily": daily,
        "timezone": "auto",
        "forecast_days": 3,
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException:
        log.exception("Ошибка при получении прогноза")
        raise

    log.info("Прогноз успешно получен")
    return response.json()

