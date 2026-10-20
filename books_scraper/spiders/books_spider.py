import random
from typing import Generator, List, Dict, Any
import scrapy
from scrapy.http import Response
from books_scraper.items import BookItem
from books_scraper.selectors import BookSelectors

class BooksSpider(scrapy.Spider):
    """Spider to dynamically discover categories and sample books."""
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.min_categories = 5
        self.max_categories = 10
        self.books_per_category = 5
    def parse(self, response: Response) -> Generator[scrapy.Request, None, None]:
        """Extract all categories dynamically and pick 5 to 10 at random."""
        category_elements = response.css(BookSelectors.CATEGORY_LINKS)
        categories: List[Dict[str, str]] = []
        for el in category_elements:
            name = el.css("::text").get()
            href = el.attrib.get("href")
            if name and href:
                categories.append({
                    "name": name.strip(),
                    "url": response.urljoin(href)
                })

        if not categories:
            self.logger.error("No categories discovered on homepage.")
            return
        sample_count = random.randint(self.min_categories, self.max_categories)
        sample_count = min(sample_count, len(categories))
        selected_categories = random.sample(categories, sample_count)
        self.logger.info(
            f"Discovered {len(categories)} categories. Randomly selected {sample_count}: "
            f"{[c['name'] for c in selected_categories]}"
        )
        for cat in selected_categories:
            yield scrapy.Request(
                url=cat["url"],
                callback=self.parse_category,
                meta={"category": cat["name"], "collected_urls": []}
            )

    def parse_category(self, response: Response) -> Generator[scrapy.Request, None, None]:
        """Collect all book URLs across category pagination before sampling."""
        category = response.meta["category"]
        collected_urls: List[str] = response.meta["collected_urls"]

        # Collect all book links from the current page
        book_links = response.css(BookSelectors.BOOK_CARDS).css(BookSelectors.BOOK_LINK).getall()
        for link in book_links:
            collected_urls.append(response.urljoin(link))

        next_page = response.css(BookSelectors.NEXT_PAGE).get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_category,
                meta={"category": category, "collected_urls": collected_urls}
            )
        else:
            sample_size = min(self.books_per_category, len(collected_urls))
            selected_urls = random.sample(collected_urls, sample_size)
            self.logger.info(
                f"Category '{category}' has {len(collected_urls)} books. "
                f"Selected {sample_size} for extraction."
            )
            for book_url in selected_urls:
                yield scrapy.Request(
                    url=book_url,
                    callback=self.parse_book,
                    meta={"category": category}
                )

    def parse_book(self, response: Response) -> Generator[BookItem, None, None]:
        """Extract raw data fields from the individual book details page."""
        availability_text = "".join(
            response.css(f"{BookSelectors.AVAILABILITY}::text").getall()
        )
        raw_image = response.css(BookSelectors.IMAGE).get()
        item = BookItem()
        item["title"] = response.css(BookSelectors.TITLE).get()
        item["price"] = response.css(BookSelectors.PRICE).get()
        item["availability"] = availability_text
        item["product_url"] = response.url
        item["image_url"] = response.urljoin(raw_image) if raw_image else ""
        item["category"] = response.meta["category"]
        yield item