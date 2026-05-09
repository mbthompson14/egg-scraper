import json
import logging
import re
import time
from html import unescape
from urllib.parse import quote

import requests

from .shared import EggProduct, Scraper, extract_quantity, infer_production_system


class EroskiScraper(Scraper):
    '''Scraper for Eroski. Parses GTM ecommerce data embedded in search result pages.'''

    def __init__(self):
        super().__init__('Eroski')
        self.base_url = 'https://supermercado.eroski.es'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }

    def scrape_eggs(self) -> list[EggProduct]:
        seen: dict[str, dict] = {}
        page = 1

        while True:
            url = f'{self.base_url}/es/search/results/?q=huevos&Rows=48&pagenumber={page}'
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logging.error(f'Eroski: page {page} returned {response.status_code}')
                break

            raw_items = self._parse_gtm_items(response.text)
            new_items = {item['item_id']: item for item in raw_items if item['item_id'] not in seen}
            if not new_items:
                break

            seen.update(new_items)
            page += 1
            time.sleep(0.2)

        return [self._to_egg_product(item) for item in seen.values()]

    def _parse_gtm_items(self, html: str) -> list[dict]:
        pattern = r'ecommerce&quot;:\{&quot;currency&quot;[^"]*&quot;items&quot;:\[(\{[^\]]+\})'
        items = []
        for raw in re.findall(pattern, html):
            try:
                items.append(json.loads(unescape(raw)))
            except json.JSONDecodeError:
                continue
        return items

    def _to_egg_product(self, item: dict) -> EggProduct:
        name = item.get('item_name', '')
        quantity = extract_quantity(name)
        price = float(item.get('price', 0))
        price_per_egg = round(price / quantity, 2) if quantity else price
        sku = str(item.get('item_id', ''))
        slug = quote(name.lower().replace(' ', '-').replace(',', ''), safe='-')
        url = f'{self.base_url}/es/productdetail/{sku}-{slug}/'
        return EggProduct(
            retailer=self.name,
            sku=sku,
            name=name,
            production_system=infer_production_system(name),
            price=price,
            price_unit='ud',
            price_per_egg=price_per_egg,
            quantity=quantity,
            source='HTML',
            url=url,
        )
