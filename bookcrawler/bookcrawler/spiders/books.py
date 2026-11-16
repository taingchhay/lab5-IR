import hashlib, re, scrapy

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, max_pages=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = max(1, int(max_pages))
        self.pages_seen = 0

    def parse(self, response):
        self.pages_seen += 1
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, callback=self.parse_book)
        next_href = response.css("li.next a::attr(href)").get()
        if next_href and self.pages_seen < self.max_pages:
            yield response.follow(next_href, callback=self.parse)

    def parse_book(self, response):
        title = (response.css("div.product_main h1::text").get() or "").strip()
        desc_parts = response.css("#product_description + p ::text").getall()
        description = " ".join(p.strip() for p in desc_parts if p.strip()) or None
        category = response.css("ul.breadcrumb li:nth-child(3) a::text").get()
        price_text = response.css("p.price_color::text").get() or ""
        m = re.search(r"\d+(?:\.\d+)?", price_text)
        price = float(m.group()) if m else None
        rating_cls = response.css("p.star-rating::attr(class)").get() or ""
        rating = next((v for k, v in RATINGS.items() if k in rating_cls), None)
        availability = " ".join(
            "".join(response.css("p.instock.availability ::text").getall()).split()) or None
        text = " ".join(x for x in [title, description] if x)
        yield {
            "doc_id": hashlib.sha1(response.url.encode("utf-8")).hexdigest()[:12],
            "title": title,
            "text": text,
            "description": description,
            "url": response.url,
            "category": category.strip() if category else None,
            "price_gbp": price,
            "rating": rating,
            "availability": availability,
            "source": "books.toscrape.com",
        }
