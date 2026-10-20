class BookSelectors:
    CATEGORY_LINKS = "div.side_categories ul.nav-list > li > ul > li > a"
    BOOK_CARDS = "article.product_pod"
    BOOK_LINK = "h3 a::attr(href)"
    NEXT_PAGE = "li.next a::attr(href)"

    TITLE = "div.product_main h1::text"
    PRICE = "div.product_main p.price_color::text"
    AVAILABILITY = "div.product_main p.instock.availability"
    IMAGE = "div.item.active img::attr(src)"
    