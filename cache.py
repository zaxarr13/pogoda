import json
import sqlite3
import time

from config import CACHE_TTL, DB_NAME, log


class Cache:
    def __init__(self, db=DB_NAME):
        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                city TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                saved_at REAL NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                searched_at REAL NOT NULL,
                temperature REAL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                city TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                added_at REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def get(self, city):
        row = self.conn.execute(
            "SELECT data, saved_at FROM cache WHERE city = ?",
            (city.lower(),),
        ).fetchone()

        if not row:
            return None

        if time.time() - row["saved_at"] > CACHE_TTL:
            log.info("Данные по городу '%s' устарели", city)
            return None

        log.info("Данные по городу '%s' получены из кэша", city)
        return json.loads(row["data"])

    def set(self, city, data):
        self.conn.execute(
            "REPLACE INTO cache (city, data, saved_at) VALUES (?, ?, ?)",
            (
                city.lower(),
                json.dumps(data, ensure_ascii=False),
                time.time(),
            ),
        )
        self.conn.commit()
        log.info("Данные по городу '%s' сохранены в кэш", city)

    def add_history(self, data):
        geo = data["geo"]
        temperature = data["forecast"]["current"].get("temperature_2m")
        self.conn.execute(
            "INSERT INTO history (city, searched_at, temperature) VALUES (?, ?, ?)",
            (geo["name"], time.time(), temperature),
        )
        self.conn.commit()

    def get_history(self, limit=20):
        return self.conn.execute(
            """
            SELECT id, city, searched_at, temperature
            FROM history
            ORDER BY searched_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def add_bookmark(self, data):
        geo = data["geo"]
        self.conn.execute(
            "REPLACE INTO bookmarks (city, data, added_at) VALUES (?, ?, ?)",
            (
                geo["name"].lower(),
                json.dumps(data, ensure_ascii=False),
                time.time(),
            ),
        )
        self.conn.commit()

    def remove_bookmark(self, city):
        self.conn.execute(
            "DELETE FROM bookmarks WHERE city = ?",
            (city.lower(),),
        )
        self.conn.commit()

    def get_bookmarks(self):
        rows = self.conn.execute(
            "SELECT city, data FROM bookmarks ORDER BY added_at DESC"
        ).fetchall()
        return [(row["city"], json.loads(row["data"])) for row in rows]

    def close(self):
        self.conn.close()