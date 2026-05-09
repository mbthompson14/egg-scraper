'''
Shared code for scrapers. This includes utility functions and classes that are used by multiple scrapers.
'''

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime

# production_systems = {
#     'cage': 'Cage',
#     'free_range': 'Free Range',
#     'organic': 'Organic',
#     'barn': 'Barn',
#     'unknown': 'Unknown'
# }

def extract_quantity(name: str) -> int:
    '''Extract egg count from a product name. Returns 0 if unknown.'''
    name_lower = name.lower()
    m = re.search(r'(\d+)\s+docenas?', name_lower)
    if m:
        return int(m.group(1)) * 12
    m = re.search(r'(\d+)\s+(?:unidades?|uds?\.?)', name_lower)
    if m:
        return int(m.group(1))
    return 0


def infer_production_system(name: str) -> str:
    name = name.lower()
    if 'ecológic' in name or 'ecologic' in name or ' bio' in name or name.endswith(' bio'):
        return 'organic'
    if 'campero' in name or 'campera' in name or 'aire libre' in name:
        return 'free_range'
    if 'suelo' in name or 'gallinero' in name or 'sueltas' in name:
        return 'barn'
    return 'caged'


@dataclass
class EggProduct:
    '''Data class for egg products.'''
    retailer: str
    sku: str
    name: str
    production_system: str
    price: float
    price_unit: str
    price_per_egg: float
    quantity: int
    source: str
    url: str = field(default='')
    scraped_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def to_dict(self):
        '''Convert the EggProduct to a dictionary.'''
        return asdict(self)
 
    
class Scraper(ABC):
    '''Base class for scrapers.'''
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def scrape_eggs(self) -> list[EggProduct]:
        '''Scrape the website and return a list of EggProduct objects.'''
        pass