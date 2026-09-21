import tkinter as tk
from tkinter import messagebox, ttk

import requests

from cache import Cache
from config import log
import api
from logic import describe_code, make_recommendation


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Погодный помощник")
        self.geometry("480x560")
        self.resizable(False, False)

        self.cache = Cache()
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Введите город:",
            font=("Segoe UI", 12),
        ).pack(anchor="w")

        row = ttk.Frame(frame)
        row.pack(fill="x", pady=5)

        self.city_var = tk.StringVar(value="Москва")
        entry = ttk.Entry(
            row,
            textvariable=self.city_var,
            font=("Segoe UI", 12),
        )
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda event: self.show_weather())

        ttk.Button(
            row,
            text="Узнать",
            command=self.show_weather,
        ).pack(side="left", padx=5)

        self.result = tk.Text(
            frame,
            height=22,
            font=("Segoe UI", 11),
            wrap="word",
            state="disabled",
            bg="#f7f9fc",
        )
        self.result.pack(fill="both", expand=True, pady=10)

        self.status = ttk.Label(
            frame,
            text="Готово",
            foreground="gray",
        )
        self.status.pack(anchor="w")

    def _write(self, text):
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", text)
        self.result.configure(state="disabled")

    def show_weather(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("Внимание", "Введите название города")
            return

        self.status.config(text="Загрузка...")
        self.update_idletasks()

        try:
            data = self.cache.get(city)

            if data is None:
                geo = api.geocode(city)
                fc = api.forecast(geo["lat"], geo["lon"])
                data = {"geo": geo, "forecast": fc}
                self.cache.set(city, data)

            self._render(data)
            self.status.config(text="Готово")

        except ValueError as error:
            log.warning("Город не найден: %s", error)
            messagebox.showerror("Ошибка", str(error))
            self.status.config(text="Ошибка")

        except requests.RequestException as error:
            log.error("Ошибка сети: %s", error)
            messagebox.showerror(
                "Ошибка сети",
                "Не удалось загрузить данные. Проверьте подключение к интернету.",
            )
            self.status.config(text="Ошибка сети")

    def _render(self, data):
        geo = data["geo"]
        forecast_data = data["forecast"]
        current = forecast_data["current"]
        daily = forecast_data["daily"]

        location = f"{geo['name']}, {geo['country']}"
        region = geo.get("region", "").strip()
        if region:
            location += f", {region}"

        output = []
        output.append(f"{location}\n")
        output.append("-" * 40 + "\n")
        output.append("Текущая погода:\n")
        output.append(f"  {describe_code(current['weather_code'])}\n")
        output.append(
            f"  Температура: {current['temperature_2m']}°C "
            f"(ощущается как {current['apparent_temperature']}°C)\n"
        )
        output.append(f"  Влажность: {current['relative_humidity_2m']}%\n")
        output.append(f"  Ветер: {current['wind_speed_10m']} км/ч\n")
        output.append("\n" + "-" * 40 + "\n")
        output.append("Прогноз на 3 дня:\n")

        for index, date in enumerate(daily["time"]):
            output.append(
                f"  {date}: "
                f"{daily['temperature_2m_min'][index]}.."
                f"{daily['temperature_2m_max'][index]}°C, "
                f"{describe_code(daily['weather_code'][index])}, "
                f"вероятность осадков "
                f"{daily['precipitation_probability_max'][index]}%\n"
            )

        output.append("\n" + "-" * 40 + "\n")
        output.append("Рекомендации:\n")
        output.append(make_recommendation(current, daily))

        self._write("".join(output))
        log.info("Отображена погода для города '%s'", geo["name"])

    def destroy(self):
        self.cache.close()
        log.info("Завершение работы приложения")
        super().destroy()