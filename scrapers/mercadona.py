'''
Mercadona scraper. Uses the public API to get the product information. 
The API is not documented, so it is reverse engineered from the web application.
No authentication is required to access the API, but it is rate limited to 10 requests per second.
'''

import requests
import time
import logging
from .shared import EggProduct, Scraper, infer_production_system

class MercadonaScraper(Scraper):
    '''Scraper for Mercadona.'''

    def __init__(self, warehouse: str = 'mad1'):
        super().__init__('Mercadona')
        self.base_url = 'https://tienda.mercadona.es/api'
        self.warehouse = warehouse
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_eggs(self) -> list[EggProduct]:
        '''Search the API and return a list of EggProduct objects.'''

        url = f"{self.base_url}/categories/?lang=es&wh={self.warehouse}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            logging.error(f'Failed to get categories: {response.status_code}')
            return []

        data = response.json()
        products = []

        # API is a two-level category tree; eggs live in subcategories named "Huevos"
        for top_category in data.get('results', []):
            for subcategory in top_category.get('categories', []):
                if 'huevo' not in subcategory['name'].lower():
                    continue

                time.sleep(0.1)
                subcat_url = f"{self.base_url}/categories/{subcategory['id']}/?lang=es&wh={self.warehouse}"
                subcat_response = requests.get(subcat_url, headers=self.headers)
                if subcat_response.status_code != 200:
                    logging.error(f'Failed to get subcategory {subcategory["id"]}: {subcat_response.status_code}')
                    continue

                for nested_cat in subcat_response.json().get('categories', []):
                    for product in nested_cat.get('products', []):
                        pi = product.get('price_instructions', {})
                        egg_product = EggProduct(
                            retailer=self.name,
                            sku=str(product['id']),
                            name=product['display_name'],
                            production_system=infer_production_system(product['display_name']),
                            price=float(pi['unit_price']),
                            price_unit=pi.get('reference_format', 'ud'),
                            price_per_egg=float(pi['bulk_price']),
                            quantity=int(pi['unit_size']),
                            source='API',
                            url=product.get('share_url', '')
                        )
                        products.append(egg_product)

        return products