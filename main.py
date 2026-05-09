
import argparse
import json
import logging
import pathlib
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("egg_tracker")

# ── make imports work whether run from project root or egg-tracker/ ──────────
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scrapers import MercadonaScraper, DIAScraper, EroskiScraper, AlcampoScraper

scrapers = [MercadonaScraper(), DIAScraper(), EroskiScraper(), AlcampoScraper()]
for scraper in scrapers:
    print(f'\n--- {scraper.name} ---')
    for product in scraper.scrape_eggs():
        print(product.to_dict())