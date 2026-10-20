import os

BOT_NAME = "books_scraper"
SPIDER_MODULES = ["books_scraper.spiders"]
NEWSPIDER_MODULE = "books_scraper.spiders"
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 0.25
COOKIES_ENABLED = False
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
SQLITE_DB_PATH = os.path.join(DATA_DIR, "books.db")
ITEM_PIPELINES = {
    "books_scraper.pipelines.CleaningPipeline": 300,
    "books_scraper.pipelines.SQLitePipeline": 400,
}
FEEDS = {
    os.path.join(DATA_DIR, "books.json"): {
        "format": "json",
        "encoding": "utf8",
        "indent": 4,
        "overwrite": True,
    },
    os.path.join(DATA_DIR, "books.csv"): {
        "format": "csv",
        "encoding": "utf8",
        "overwrite": True,
    },
    os.path.join(DATA_DIR, "books.xml"): {
        "format": "xml",
        "encoding": "utf8",
        "indent": 4,
        "overwrite": True,
    },
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
