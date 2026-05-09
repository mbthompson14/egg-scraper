"""
Compares scraped egg listing production-system breakdown against reported
cage-free progress for the top Spanish retailers.

Run quarterly:
    python analysis/report.py [--output analysis/report.md]
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scrapers import MercadonaScraper, DIAScraper, EroskiScraper, AlcampoScraper

SCRAPERS = [MercadonaScraper(), DIAScraper(), EroskiScraper(), AlcampoScraper()]
SYSTEMS = ['caged', 'barn', 'free_range', 'organic']

# Cage-free commitment data — update when retailers publish new figures.
# All four committed to 100% cage-free by 2025.
# Sources: retailer press releases; Animal Welfare Observatory (OBA); EggTrack 2024 (CIWF).
COMMITMENTS = {
    'Mercadona': {'reported_pct': 65,   'reported_year': 2024, 'third_party': 'Not reported'},
    'DIA':       {'reported_pct': None, 'reported_year': None, 'third_party': 'Behind ✗'},
    'Eroski':    {'reported_pct': None, 'reported_year': None, 'third_party': 'Behind ✗'},
    'Alcampo':   {'reported_pct': 63,   'reported_year': 2023, 'third_party': 'Behind ✗'},
}


def scrape_all() -> pd.DataFrame:
    rows = []
    for scraper in SCRAPERS:
        print(f'  {scraper.name}...', flush=True)
        for p in scraper.scrape_eggs():
            rows.append(p.to_dict())
    df = pd.DataFrame(rows)
    return df[df['quantity'] >= 6].copy()


COLORS = {'caged': '#c62828', 'barn': '#e65100', 'free_range': '#2e7d32', 'organic': '#1565c0'}
LABELS = {'caged': 'Caged', 'barn': 'Barn', 'free_range': 'Free-range', 'organic': 'Organic'}


def plot_production_mix(df: pd.DataFrame, out: pathlib.Path) -> None:
    mix = (
        df.groupby(['retailer', 'production_system'])['quantity']
        .sum().unstack(fill_value=0)
        .reindex(columns=SYSTEMS, fill_value=0)
    )
    mix_pct = mix.div(mix.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = np.zeros(len(mix_pct))
    for system in SYSTEMS:
        vals = mix_pct[system].values
        ax.bar(mix_pct.index, vals, bottom=bottom,
               color=COLORS[system], label=LABELS[system], width=0.5)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 6:
                ax.text(i, b + v / 2, f'{v:.0f}%', ha='center', va='center',
                        fontsize=10, fontweight='bold', color='white')
        bottom += vals

    ax.set_ylabel('Share of catalog-listed egg units (%)')
    ax.set_ylim(0, 108)
    ax.set_title('Production system mix by retailer', fontweight='bold', pad=10)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)


def build_report(df: pd.DataFrame) -> str:
    scraped_at = df['scraped_at'].max()

    rows = []
    for retailer in sorted(df['retailer'].unique()):
        g = df[df['retailer'] == retailer]
        total = g['quantity'].sum()

        sys_pct = {
            s: g[g['production_system'] == s]['quantity'].sum() / total * 100
            for s in SYSTEMS
        }
        listed_cf = sys_pct['free_range'] + sys_pct['organic']

        c = COMMITMENTS.get(retailer, {})
        reported = f"{c['reported_pct']}%" if c.get('reported_pct') is not None else '—'
        rep_year = str(c['reported_year']) if c.get('reported_year') else '—'

        rows.append({
            'Retailer': retailer,
            'Caged %': f"{sys_pct['caged']:.0f}%",
            'Barn %': f"{sys_pct['barn']:.0f}%",
            'Free-range %': f"{sys_pct['free_range']:.0f}%",
            'Organic %': f"{sys_pct['organic']:.0f}%",
            'Listed cage-free %': f"{listed_cf:.0f}%",
            'Reported cage-free %': reported,
            'As of': rep_year,
            'Third-party status': c.get('third_party', '—'),
        })

    table = pd.DataFrame(rows)
    cols = list(table.columns)
    widths = [max(len(c), max(len(str(v)) for v in table[c])) for c in cols]

    def md_row(vals):
        return '| ' + ' | '.join(str(v).ljust(w) for v, w in zip(vals, widths)) + ' |'

    sep = '| ' + ' | '.join('-' * w for w in widths) + ' |'

    lines = [
        '# Egg Production System vs Cage-Free Progress — Spanish Retailers',
        '',
        f'*Scraped: {scraped_at}*',
        '',
        '![Production system mix](production_mix.png)',
        '',
        md_row(cols),
        sep,
        *[md_row(r) for _, r in table.iterrows()],
        '',
        '**Listed cage-free %** = share of catalog-listed egg units '
        '(pack quantity × SKUs) that is free-range or organic. '
        'Does not reflect actual sales weighting.',
        '',
        '**Reported cage-free %** = most recent self-reported figure for fresh eggs. '
        'Sources: retailer press releases; Animal Welfare Observatory (OBA); EggTrack 2024 (CIWF).',
        '',
        'All four retailers committed to 100% cage-free by 2025.',
    ]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='analysis/report.md')
    args = parser.parse_args()

    print('Scraping...')
    df = scrape_all()
    print(f'  {len(df)} products\n')

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    plot_production_mix(df, out.parent / 'production_mix.png')
    out.write_text(build_report(df))
    print(f'→ {out}')

    csv_path = out.parent / 'data.csv'
    df.drop(columns=['scraped_at']).to_csv(csv_path, index=False)
    print(f'→ {csv_path}')


if __name__ == '__main__':
    main()
