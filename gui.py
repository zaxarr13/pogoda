import tkinter as tk
from tkinter import ttk, messagebox
import requests

from config import log
import api
from cache import Cache
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

        ttk.Label(frame, text="Введите город:", font=("Segoe UI", 12)).pack(anchor="w")

        row = ttk.Frame(frame)
        row.pack(fill="x", pady=5)

        self.city_var = tk.StringVar(value="Москва")
        entry = ttk.Entry(row, textvariable=self.city_var, font=("Segoe UI", 12))
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.show_weather())

        ttk.Button(row, text="Узнать", command=self.show_weather).pack(side="left", padx=5)

        self.result = tk.Text(frame, height=22, font=("Segoe UI", 11),
                              wrap="word", state="disabled", bg="#f7f9fc")
        self.result.pack(fill="both", expand=True, pady=10)

        self.status = ttk.Label(frame, text="Готово", foreground="gray")
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

        except ValueError as e:
            log.warning("Город не найден: %s", e)
            messagebox.showerror("Ошибка", str(e))
            self.status.config(text="Ошибка")
        except requests.RequestException as e:
            log.error("Ошибка сети: %s", e)
            messagebox.showerror("Ошибка сети", "Не удалось загрузить данные. Проверьте подключение к интернету.")
            self.status.config(text="Ошибка сети")

    def _render(self, data):
        geo = data["geo"]
        fc = data["forecast"]
        cur = fc["current"]
        daily = fc["daily"]

        out = []
        out.append(f"{geo['name']}, {geo['country']}\n")
        out.append("-" * 40 + "\n")
        out.append("Текущая погода:\n")
        out.append(f"  {describe_code(cur['weather_code'])}\n")
        out.append(f"  Температура: {cur['temperature_2m']}°C (ощущается как {cur['apparent_temperature']}°C)\n")
        out.append(f"  Влажность: {cur['relative_humidity_2m']}%\n")
        out.append(f"  Ветер: {cur['wind_speed_10m']} км/ч\n")
        out.append("\n" + "-" * 40 + "\n")
        out.append("Прогноз на 3 дня:\n")

        for i, date in enumerate(daily["time"]):
            out.append(
                f"  {date}: {daily['temperature_2m_min'][i]}..{daily['temperature_2m_max'][i]}°C, "
                f"{describe_code(daily['weather_code'][i])}, "
                f"вероятность осадков {daily['precipitation_probability_max'][i]}%\n"
            )

        out.append("\n" + "-" * 40 + "\n")
        out.append("Рекомендации:\n")
        out.append(make_recommendation(cur, daily))

        self._write("".join(out))
        log.info("Отображена погода для города '%s'", geo["name"])

    def destroy(self):
        self.cache.close()
        log.info("Завершение работы приложения")
        super().destroy()