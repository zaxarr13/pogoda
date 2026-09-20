import json
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import requests
import api
from cache import Cache
from config import log
from logic import (
    calculate_risk,
    describe_code,
    make_recommendation,
)


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Погодный помощник")
        self.geometry("650x650")
        self.resizable(False, False)

        self.cache = Cache()
        self.current_data = None

        self.build_ui()

        log.info("Интерфейс приложения создан")

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(
            main_frame,
            text="Введите город:",
            font=("Segoe UI", 12)
        ).pack(anchor="w")

        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=5)

        self.city_var = tk.StringVar(value="Москва")

        city_entry = ttk.Entry(
            search_frame,
            textvariable=self.city_var,
            font=("Segoe UI", 12)
        )
        city_entry.pack(side="left", fill="x", expand=True)
        city_entry.bind(
            "<Return>",
            lambda event: self.show_weather()
        )

        ttk.Button(
            search_frame,
            text="Узнать",
            command=self.show_weather
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="В закладки",
            command=self.add_bookmark
        ).pack(side="left")

        self.tabs = ttk.Notebook(main_frame)
        self.tabs.pack(fill="both", expand=True, pady=10)

        self.summary_tab = ttk.Frame(self.tabs, padding=8)
        self.history_tab = ttk.Frame(self.tabs, padding=8)
        self.bookmarks_tab = ttk.Frame(self.tabs, padding=8)

        self.tabs.add(self.summary_tab, text="Сводка")
        self.tabs.add(self.history_tab, text="История")
        self.tabs.add(self.bookmarks_tab, text="Закладки")

        self.result = tk.Text(
            self.summary_tab,
            height=28,
            font=("Segoe UI", 11),
            wrap="word",
            state="disabled",
            bg="#f7f9fc"
        )
        self.result.pack(fill="both", expand=True)

        ttk.Button(
            self.history_tab,
            text="Обновить историю",
            command=self.show_history
        ).pack(anchor="w", pady=(0, 8))

        self.history_text = tk.Text(
            self.history_tab,
            height=28,
            font=("Segoe UI", 10),
            wrap="word",
            state="disabled"
        )
        self.history_text.pack(fill="both", expand=True)

        ttk.Button(
            self.bookmarks_tab,
            text="Обновить закладки",
            command=self.show_bookmarks
        ).pack(anchor="w", pady=(0, 8))

        self.bookmarks_text = tk.Text(
            self.bookmarks_tab,
            height=25,
            font=("Segoe UI", 10),
            wrap="word",
            state="disabled"
        )
        self.bookmarks_text.pack(fill="both", expand=True)

        ttk.Button(
            self.bookmarks_tab,
            text="Удалить выбранный город",
            command=self.remove_selected_bookmark
        ).pack(anchor="w", pady=8)

        self.status = ttk.Label(
            main_frame,
            text="Готово",
            foreground="gray"
        )
        self.status.pack(anchor="w")

        self.show_bookmarks()

    def write_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def show_weather(self):
        city = self.city_var.get().strip()

        log.info("Запрос погоды для города: %s", city)

        if not city:
            log.warning("Пустое название города")
            messagebox.showwarning(
                "Внимание",
                "Введите название города"
            )
            return

        self.status.config(text="Загрузка...")
        self.update_idletasks()

        try:
            data = self.cache.get(city)

            if data is None:
                log.info("Получение новых данных через API")

                geo = api.geocode(city)
                forecast_data = api.forecast(
                    geo["lat"],
                    geo["lon"]
                )

                data = {
                    "geo": geo,
                    "forecast": forecast_data,
                }

                self.cache.set(city, data)

            self.current_data = data

            self.cache.add_history(
                data["geo"]["name"],
                data
            )

            self.render_weather(data)
            self.show_history()

            self.status.config(text="Готово")
            log.info("Погода успешно отображена")

        except ValueError as error:
            log.warning("Ошибка поиска города: %s", error)

            messagebox.showerror(
                "Ошибка",
                str(error)
            )

            self.status.config(text="Ошибка")

        except requests.RequestException:
            log.exception("Ошибка подключения к API")

            messagebox.showerror(
                "Ошибка сети",
                "Не удалось загрузить данные. "
                "Проверьте подключение к интернету."
            )

            self.status.config(text="Ошибка сети")

        except Exception:
            log.exception("Непредвиденная ошибка")

            messagebox.showerror(
                "Ошибка",
                "Произошла непредвиденная ошибка."
            )

            self.status.config(text="Ошибка")

    def render_weather(self, data):
        geo = data["geo"]
        forecast_data = data["forecast"]

        current = forecast_data["current"]
        daily = forecast_data["daily"]

        score, level, reasons = calculate_risk(
            current,
            daily
        )

        if reasons:
            reasons_text = ", ".join(reasons)
        else:
            reasons_text = "существенных факторов риска нет"

        output = []

        output.append(
            f"{geo['name']}, {geo['country']}\n"
        )
        output.append("-" * 50 + "\n")

        output.append("Текущая погода:\n")
        output.append(
            f"Состояние: "
            f"{describe_code(current['weather_code'])}\n"
        )
        output.append(
            f"Температура: "
            f"{current['temperature_2m']} °C\n"
        )
        output.append(
            f"Ощущается как: "
            f"{current['apparent_temperature']} °C\n"
        )
        output.append(
            f"Влажность: "
            f"{current['relative_humidity_2m']}%\n"
        )
        output.append(
            f"Ветер: "
            f"{current['wind_speed_10m']} км/ч\n"
        )

        output.append("\nИндекс погодного риска:\n")
        output.append(
            f"Уровень: {level}\n"
        )
        output.append(
            f"Баллы: {score}\n"
        )
        output.append(
            f"Факторы: {reasons_text}\n"
        )

        output.append("\n" + "-" * 50 + "\n")
        output.append("Прогноз на 3 дня:\n")

        for index, date in enumerate(daily["time"]):
            output.append(
                f"{date}: "
                f"{daily['temperature_2m_min'][index]}..."
                f"{daily['temperature_2m_max'][index]} °C, "
                f"{describe_code(daily['weather_code'][index])}, "
                f"осадки: "
                f"{daily['precipitation_probability_max'][index]}%\n"
            )

        output.append("\n" + "-" * 50 + "\n")
        output.append("Рекомендации:\n")
        output.append(
            make_recommendation(current, daily)
        )

        self.write_text(
            self.result,
            "".join(output)
        )

    def add_bookmark(self):
        if not self.current_data:
            log.warning(
                "Попытка добавить город без загруженных данных"
            )

            messagebox.showwarning(
                "Внимание",
                "Сначала выполните поиск города."
            )
            return

        geo = self.current_data["geo"]

        self.cache.add_bookmark(geo)
        self.show_bookmarks()

        messagebox.showinfo(
            "Закладки",
            "Город добавлен в закладки."
        )

    def show_history(self):
        rows = self.cache.get_history()

        if not rows:
            self.write_text(
                self.history_text,
                "История запросов пока пуста."
            )
            return

        output = []

        for city, data_json, timestamp in rows:
            data = json.loads(data_json)
            temperature = data["forecast"]["current"][
                "temperature_2m"
            ]

            date = datetime.fromtimestamp(
                timestamp
            ).strftime("%d.%m.%Y %H:%M")

            output.append(
                f"{date} — {city}: {temperature} °C\n"
            )

        self.write_text(
            self.history_text,
            "".join(output)
        )

    def show_bookmarks(self):
        rows = self.cache.get_bookmarks()

        if not rows:
            self.write_text(
                self.bookmarks_text,
                "Закладок пока нет."
            )
            return

        output = []

        for city, country, lat, lon in rows:
            output.append(
                f"{city}, {country}\n"
            )

        self.write_text(
            self.bookmarks_text,
            "".join(output)
        )

    def remove_selected_bookmark(self):
        try:
            selected_text = self.bookmarks_text.get(
                "sel.first",
                "sel.last"
            ).strip()
        except tk.TclError:
            messagebox.showwarning(
                "Внимание",
                "Сначала выделите город."
            )
            return

        if not selected_text:
            messagebox.showwarning(
                "Внимание",
                "Сначала выделите город."
            )
            return

        city = selected_text.split(",")[0].strip()

        self.cache.remove_bookmark(city)
        self.show_bookmarks()

        messagebox.showinfo(
            "Закладки",
            "Город удалён из закладок."
        )

    def destroy(self):
        log.info("Завершение работы приложения")
        self.cache.close()
        super().destroy()