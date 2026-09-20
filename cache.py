import json
import sqlite3
import time

from config import log, DB_NAME, CACHE_TTL


class Cache:
    def __init__(self, db=DB_NAME):
        log.info("Подключение к базе данных: %s", db)

        self.conn = sqlite3.connect(db)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                city TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                saved_at REAL NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                data TEXT NOT NULL,
                requested_at REAL NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                city TEXT PRIMARY KEY,
                country TEXT NOT NULL DEFAULT '',
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                added_at REAL NOT NULL
            )
        """)

        self.conn.commit()
        log.info("База данных успешно инициализирована")

    def get(self, city):
        city_key = city.strip().lower()

        row = self.conn.execute(
            """
            SELECT data, saved_at
            FROM cache
            WHERE city = ?
            """,
            (city_key,)
        ).fetchone()

        if not row:
            log.info("Данных в кэше нет: %s", city)
            return None

        data, saved_at = row
        cache_age = time.time() - saved_at

        if cache_age > CACHE_TTL:
            log.info("Кэш устарел: %s", city)
            return None

        log.info("Данные загружены из кэша: %s", city)
        return json.loads(data)

    def set(self, city, data):
        city_key = city.strip().lower()

        self.conn.execute(
            """
            REPLACE INTO cache
            (city, data, saved_at)
            VALUES (?, ?, ?)
            """,
            (
                city_key,
                json.dumps(data, ensure_ascii=False),
                time.time(),
            )
        )

        self.conn.commit()
        log.info("Данные сохранены в кэш: %s", city)

    def add_history(self, city, data):
        self.conn.execute(
            """
            INSERT INTO history
            (city, data, requested_at)
            VALUES (?, ?, ?)
            """,
            (
                city,
                json.dumps(data, ensure_ascii=False),
                time.time(),
            )
        )

        self.conn.commit()
        log.info("Запрос добавлен в историю: %s", city)

    def get_history(self, limit=100):
        rows = self.conn.execute(
            """
            SELECT city, data, requested_at
            FROM history
            ORDER BY requested_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        log.info("Получено записей истории: %d", len(rows))
        return rows

    def add_bookmark(self, geo):
        self.conn.execute(
            """
            REPLACE INTO bookmarks
            (city, country, lat, lon, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                geo["name"],
                geo.get("country", ""),
                geo["lat"],
                geo["lon"],
                time.time(),
            )
        )

        self.conn.commit()
        log.info("Город добавлен в закладки: %s", geo["name"])

    def remove_bookmark(self, city):
        self.conn.execute(
            "DELETE FROM bookmarks WHERE city = ?",
            (city,)
        )

        self.conn.commit()
        log.info("Город удалён из закладок: %s", city)

    def get_bookmarks(self):
        rows = self.conn.execute(
            """
            SELECT city, country, lat, lon
            FROM bookmarks
            ORDER BY city
            """
        ).fetchall()

        log.info("Получено закладок: %d", len(rows))
        return rows

    def close(self):
        log.info("Закрытие базы данных")
        self.conn.close()