import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import requests

import api
from cache import Cache
from config import log
from logic import describe_code, make_recommendation


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Погодный помощник")
        self.geometry("560x650")
        self.resizable(False, False)

        self.cache = Cache()
        self.current_data = None
        self._build_ui()
        self._refresh_history()
        self._refresh_bookmarks()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        weather_tab = ttk.Frame(notebook, padding=15)
        history_tab = ttk.Frame(notebook, padding=15)
        bookmarks_tab = ttk.Frame(notebook, padding=15)

        notebook.add(weather_tab, text="Погода")
        notebook.add(history_tab, text="История")
        notebook.add(bookmarks_tab, text="Закладки")

        self._build_weather_tab(weather_tab)
        self._build_history_tab(history_tab)
        self._build_bookmarks_tab(bookmarks_tab)

    def _build_weather_tab(self, tab):
        ttk.Label(
            tab,
            text="Введите город:",
            font=("Segoe UI", 12),
        ).pack(anchor="w")

        row = ttk.Frame(tab)
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

        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", pady=5)

        self.bookmark_button = ttk.Button(
            buttons,
            text="Добавить в закладки",
            command=self.add_current_bookmark,
            state="disabled",
        )
        self.bookmark_button.pack(side="left")

        self.result = tk.Text(
            tab,
            height=24,
            font=("Segoe UI", 11),
            wrap="word",
            state="disabled",
            bg="#f7f9fc",
        )
        self.result.pack(fill="both", expand=True, pady=10)

        self.status = ttk.Label(tab, text="Готово", foreground="gray")
        self.status.pack(anchor="w")

    def _build_history_tab(self, tab):
        ttk.Label(
            tab,
            text="Последние запросы",
            font=("Segoe UI", 12),
        ).pack(anchor="w")

        self.history_list = tk.Listbox(tab, height=25, font=("Segoe UI", 11))
        self.history_list.pack(fill="both", expand=True, pady=10)
        self.history_list.bind("<Double-Button-1>", self._open_history_city)

        ttk.Button(
            tab,
            text="Обновить историю",
            command=self._refresh_history,
        ).pack(anchor="e")

    def _build_bookmarks_tab(self, tab):
        ttk.Label(
            tab,
            text="Сохранённые города",
            font=("Segoe UI", 12),
        ).pack(anchor="w")

        self.bookmarks_list = tk.Listbox(tab, height=22, font=("Segoe UI", 11))
        self.bookmarks_list.pack(fill="both", expand=True, pady=10)
        self.bookmarks_list.bind("<Double-Button-1>", self._open_bookmark_city)

        buttons = ttk.Frame(tab)
        buttons.pack(fill="x")

        ttk.Button(
            buttons,
            text="Удалить выбранный",
            command=self.remove_selected_bookmark,
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Обновить",
            command=self._refresh_bookmarks,
        ).pack(side="right")

    def _write(self, text):
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", text)
        self.result.configure(state="disabled")

    def show_weather(self, city=None):
        city = (city or self.city_var.get()).strip()
        if not city:
            messagebox.showwarning("Внимание", "Введите название города")
            return

        self.city_var.set(city)
        self.status.config(text="Загрузка...")
        self.update_idletasks()

        try:
            data = self.cache.get(city)
            if data is None:
                geo = api.geocode(city)
                weather = api.forecast(geo["lat"], geo["lon"])
                data = {"geo": geo, "forecast": weather}
                self.cache.set(city, data)

            self.current_data = data
            self.cache.add_history(data)
            self._render(data)
            self._refresh_history()
            self.bookmark_button.config(state="normal")
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

        output = [
            f"{location}\n",
            "-" * 45 + "\n",
            "Текущая погода:\n",
            f"  {describe_code(current['weather_code'])}\n",
            f"  Температура: {current['temperature_2m']}°C "
            f"(ощущается как {current['apparent_temperature']}°C)\n",
            f"  Влажность: {current['relative_humidity_2m']}%\n",
            f"  Ветер: {current['wind_speed_10m']} км/ч\n",
            "\n" + "-" * 45 + "\n",
            "Прогноз на 3 дня:\n",
        ]

        for index, date in enumerate(daily["time"]):
            output.append(
                f"  {date}: "
                f"{daily['temperature_2m_min'][index]}.."
                f"{daily['temperature_2m_max'][index]}°C, "
                f"{describe_code(daily['weather_code'][index])}, "
                f"вероятность осадков "
                f"{daily['precipitation_probability_max'][index]}%\n"
            )

        output.extend([
            "\n" + "-" * 45 + "\n",
            "Рекомендации:\n",
            make_recommendation(current, daily),
        ])

        self._write("".join(output))
        log.info("Отображена погода для города '%s'", geo["name"])

    def add_current_bookmark(self):
        if not self.current_data:
            return

        city = self.current_data["geo"]["name"]
        existing = [name for name, _ in self.cache.get_bookmarks()]
        if city.lower() in existing:
            messagebox.showinfo("Закладки", "Этот город уже добавлен в закладки.")
            return

        self.cache.add_bookmark(self.current_data)
        self._refresh_bookmarks()
        messagebox.showinfo("Закладки", f"Город «{city}» добавлен в закладки.")

    def _refresh_history(self):
        if not hasattr(self, "history_list"):
            return

        self.history_list.delete(0, tk.END)
        rows = self.cache.get_history()

        for row in rows:
            date = datetime.fromtimestamp(row["searched_at"]).strftime(
                "%d.%m.%Y %H:%M"
            )
            temperature = row["temperature"]
            temperature_text = (
                f", {temperature}°C" if temperature is not None else ""
            )
            self.history_list.insert(
                tk.END,
                f"{row['city']} — {date}{temperature_text}",
            )

        if not rows:
            self.history_list.insert(tk.END, "История пока пуста")

    def _refresh_bookmarks(self):
        if not hasattr(self, "bookmarks_list"):
            return

        self.bookmarks_list.delete(0, tk.END)
        bookmarks = self.cache.get_bookmarks()

        for city, data in bookmarks:
            geo = data["geo"]
            region = geo.get("region", "")
            location = f"{geo['name']}, {geo['country']}"
            if region:
                location += f", {region}"
            self.bookmarks_list.insert(tk.END, location)

        if not bookmarks:
            self.bookmarks_list.insert(tk.END, "Закладки пока пусты")

    def _open_history_city(self, event=None):
        selection = self.history_list.curselection()
        if not selection:
            return

        text = self.history_list.get(selection[0])
        if text == "История пока пуста":
            return

        city = text.split(" — ", 1)[0]
        self.show_weather(city)

    def _open_bookmark_city(self, event=None):
        selection = self.bookmarks_list.curselection()
        if not selection:
            return

        text = self.bookmarks_list.get(selection[0])
        if text == "Закладки пока пусты":
            return

        city = text.split(",", 1)[0]
        self.show_weather(city)

    def remove_selected_bookmark(self):
        selection = self.bookmarks_list.curselection()
        if not selection:
            return

        text = self.bookmarks_list.get(selection[0])
        if text == "Закладки пока пусты":
            return

        city = text.split(",", 1)[0]
        self.cache.remove_bookmark(city)
        self._refresh_bookmarks()
        log.info("Город '%s' удалён из закладок", city)

    def destroy(self):
        self.cache.close()
        log.info("Завершение работы приложения")
        super().destroy()