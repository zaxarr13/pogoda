from config import log
from gui import WeatherApp


def main():
    log.info("Запуск приложения")
    app = WeatherApp()
    app.mainloop()


if __name__ == "__main__":
    main()