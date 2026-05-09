import json
import logging
import re

import requests

from .shared import EggProduct, Scraper, extract_quantity, infer_production_system


class DIAScraper(Scraper):
    '''Scraper for DIA. Parses SSR JSON embedded in the egg category page.'''

    def __init__(self):
        super().__init__('DIA')
        self.base_url = 'https://www.dia.es'
        self.category_path = '/huevos-leche-y-mantequilla/huevos/c/L2055'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }

    def scrape_eggs(self) -> list[EggProduct]:
        session = requests.Session()
        session.headers.update(self.headers)
        session.get(self.base_url)

        response = session.get(f'{self.base_url}{self.category_path}')
        if response.status_code != 200:
            logging.error(f'DIA: category page returned {response.status_code}')
            return []

        items = self._parse_items(response.text)
        if items is None:
            logging.error('DIA: could not find product data in page')
            return []

        products = []
        for item in items:
            if 'prices' not in item:
                continue
            name = item.get('display_name', '')
            quantity = extract_quantity(name)
            price = float(item['prices']['price'])
            price_per_egg = round(price / quantity, 2) if quantity else price
            products.append(EggProduct(
                retailer=self.name,
                sku=str(item['sku_id']),
                name=name,
                production_system=infer_production_system(name),
                price=price,
                price_unit=item['prices'].get('measure_unit', '').lower(),
                price_per_egg=price_per_egg,
                quantity=quantity,
                source='SSR',
                url=self.base_url + item.get('url', ''),
            ))
        return products

    def _parse_items(self, html: str) -> list | None:
        for script in re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
            if 'plp_items' not in script:
                continue
            try:
                data = json.loads(script)
                return data['INITIAL_STATE']['l2']['plp_items']
            except (json.JSONDecodeError, KeyError):
                continue
        return None
