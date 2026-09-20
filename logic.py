from config import log


CODES = {
    0: "Ясно",
    1: "Малооблачно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Изморозь",
    51: "Слабая морось",
    53: "Морось",
    55: "Сильная морось",
    61: "Небольшой дождь",
    63: "Дождь",
    65: "Сильный дождь",
    71: "Небольшой снег",
    73: "Снег",
    75: "Сильный снег",
    80: "Ливень",
    81: "Сильный ливень",
    82: "Очень сильный ливень",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Гроза с сильным градом",
}


def describe_code(code):
    return CODES.get(code, "Нет данных")


def calculate_risk(current, daily):
    log.info("Расчёт индекса риска")

    score = 0
    reasons = []

    temperature = current.get("temperature_2m", 0)
    humidity = current.get("relative_humidity_2m", 0)
    wind = current.get("wind_speed_10m", 0)
    precipitation = current.get("precipitation", 0) or 0

    rain_probability = daily.get(
        "precipitation_probability_max",
        [0]
    )[0] or 0

    if temperature <= -15 or temperature >= 30:
        score += 3
        reasons.append("экстремальная температура")
    elif temperature <= -5 or temperature >= 25:
        score += 2
        reasons.append("неблагоприятная температура")

    if humidity >= 85:
        score += 1
        reasons.append("высокая влажность")

    if wind > 30:
        score += 2
        reasons.append("сильный ветер")

    if precipitation > 0 or rain_probability >= 60:
        score += 1
        reasons.append("осадки")

    if score <= 2:
        level = "Низкий"
    elif score <= 5:
        level = "Средний"
    else:
        level = "Высокий"

    log.info(
        "Индекс риска: %s, %d баллов",
        level,
        score
    )

    return score, level, reasons


def make_recommendation(current, daily):
    tips = []

    temperature = current["temperature_2m"]
    wind = current["wind_speed_10m"]
    rain_probability = daily["precipitation_probability_max"][0]
    precipitation = current["precipitation"]

    if rain_probability >= 60 or precipitation > 0:
        tips.append("Высокая вероятность осадков. Возьмите зонт.")

    if temperature <= 0:
        tips.append("Отрицательная температура. Наденьте тёплую одежду.")
    elif temperature < 10:
        tips.append("Прохладно. Рекомендуется куртка.")
    elif temperature > 27:
        tips.append("Жарко. Возьмите воду и головной убор.")

    if wind > 30:
        tips.append("Сильный ветер. Соблюдайте осторожность.")

    if not tips:
        tips.append("Погодные условия комфортные.")

    return "\n".join(tips)