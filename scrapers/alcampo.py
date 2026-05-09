import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .shared import EggProduct, Scraper, extract_quantity, infer_production_system


class AlcampoScraper(Scraper):
    '''Scraper for Alcampo (Auchan). Parses JSON-LD embedded in product detail pages.'''

    def __init__(self):
        super().__init__('Alcampo')
        self.base_url = 'https://www.compraonline.alcampo.es'
        self.category_path = '/categories/leche-huevos-l%C3%A1cteos-yogures-y-bebidas-vegetales/huevos/OC1608'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
        }

    def scrape_eggs(self) -> list[EggProduct]:
        product_urls = self._get_product_urls()
        if not product_urls:
            logging.error('Alcampo: no product URLs found on category page')
            return []

        results = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(self._fetch_product, url): url for url in product_urls}
            for future in as_completed(futures):
                product = future.result()
                if product:
                    results.append(product)
        return results

    def _get_product_urls(self) -> list[str]:
        r = requests.get(self.base_url + self.category_path, headers=self.headers, timeout=15)
        if r.status_code != 200:
            logging.error(f'Alcampo: category page returned {r.status_code}')
            return []
        return list(dict.fromkeys(
            re.findall(r'"url":"(https://www\.compraonline\.alcampo\.es/products/[^"]+)"', r.text)
        ))

    def _fetch_product(self, url: str) -> EggProduct | None:
        try:
            time.sleep(0.1)
            r = requests.get(url, headers=self.headers, timeout=15)
            if r.status_code != 200:
                return None
            return self._parse_product(r.text, url)
        except Exception as e:
            logging.warning(f'Alcampo: error fetching {url}: {e}')
            return None

    def _parse_product(self, html: str, url: str) -> EggProduct | None:
        for script in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            try:
                data = json.loads(script)
                if data.get('@type') != 'Product':
                    continue
                name = data['name']
                sku = str(data['sku'])
                price = float(data['offers']['price'])
                quantity = extract_quantity(name)
                price_per_egg = round(price / quantity, 2) if quantity else price
                return EggProduct(
                    retailer=self.name,
                    sku=sku,
                    name=name,
                    production_system=infer_production_system(name),
                    price=price,
                    price_unit='ud',
                    price_per_egg=price_per_egg,
                    quantity=quantity,
                    source='SSR',
                    url=url,
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return None
