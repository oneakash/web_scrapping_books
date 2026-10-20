import re
import sqlite3
from abc import ABC, abstractmethod
from typing import Any
from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.exceptions import DropItem


class BasePipeline(ABC):
    @abstractmethod
    def process_item(self, item: Any, spider: Spider) -> Any:
        pass

class CleaningPipeline(BasePipeline):
    PRICE_REGEX = re.compile(r"[^\d.]")
    def process_item(self, item: Any, spider: Spider) -> Any:
        adapter = ItemAdapter(item)
        for field in ["title", "category", "product_url", "image_url"]:
            val = adapter.get(field)
            if not val or not str(val).strip():
                raise DropItem(f"Missing required field '{field}' in {item}")
            adapter[field] = " ".join(str(val).strip().split())
        raw_price = str(adapter.get("price", ""))
        cleaned_price = self.PRICE_REGEX.sub("", raw_price)
        try:
            adapter["price"] = float(cleaned_price)
        except ValueError as exc:
            raise DropItem(f"Invalid price value '{raw_price}' in {item}") from exc
        raw_avail = str(adapter.get("availability", "")).strip().lower()
        adapter["availability"] = "in stock" in raw_avail
        return item


class SQLitePipeline(BasePipeline):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler: Any) -> "SQLitePipeline":
        db_path = crawler.settings.get("SQLITE_DB_PATH", "data/books.db")
        return cls(db_path=db_path)

    def open_spider(self, spider: Spider) -> None:
        """Initialize database connection and schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                availability BOOLEAN NOT NULL,
                product_url TEXT UNIQUE NOT NULL,
                image_url TEXT NOT NULL,
                category TEXT NOT NULL
            )
            """
        )
        self.cursor.execute("DELETE FROM books")
        self.conn.commit()
        spider.logger.info(f"Connected to SQLite database at {self.db_path}")

    def close_spider(self, spider: Spider) -> None:
        if self.conn:
            self.conn.commit()
            self.conn.close()
            spider.logger.info("SQLite database connection closed.")

    def process_item(self, item: Any, spider: Spider) -> Any:
        adapter = ItemAdapter(item)
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO books (
                    title, price, availability, product_url, image_url, category
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    adapter["title"],
                    adapter["price"],
                    adapter["availability"],
                    adapter["product_url"],
                    adapter["image_url"],
                    adapter["category"],
                ),
            )
            self.conn.commit()
        except sqlite3.Error as err:
            spider.logger.error(f"Database insertion error: {err}")
            raise DropItem(f"Failed to store item in DB: {item}") from err
        return item