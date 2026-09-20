from config import log
from gui import WeatherApp


def main():
    log.info("Запуск приложения")

    try:
        app = WeatherApp()
        app.mainloop()
    except Exception:
        log.exception("Критическая ошибка приложения")
        raise
    finally:
        log.info("Приложение завершено")


if __name__ == "__main__":
    main()