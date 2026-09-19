import sqlite3
import json
import time

from config import log, DB_NAME, CACHE_TTL


class Cache:
    def __init__(self, db=DB_NAME):
        self.conn = sqlite3.connect(db)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                city TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                saved_at REAL NOT NULL
            )
        """)
        self.conn.commit()

    def get(self, city):
        cur = self.conn.execute(
            "SELECT data, saved_at FROM cache WHERE city = ?",
            (city.lower(),)
        )
        row = cur.fetchone()
        if not row:
            return None

        data, saved_at = row
        if time.time() - saved_at > CACHE_TTL:
            log.info("Данные по городу '%s' устарели", city)
            return None

        log.info("Данные по городу '%s' получены из кэша", city)
        return json.loads(data)

    def set(self, city, data):
        self.conn.execute(
            "REPLACE INTO cache (city, data, saved_at) VALUES (?, ?, ?)",
            (city.lower(), json.dumps(data), time.time())
        )
        self.conn.commit()
        log.info("Данные по городу '%s' сохранены в кэш", city)

    def close(self):
        self.conn.close()