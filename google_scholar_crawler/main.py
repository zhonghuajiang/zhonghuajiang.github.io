import json
import os
import re
from pathlib import Path

from direct_profile import fetch_stats


def get_scholar_id():
    scholar_id = os.environ.get('GOOGLE_SCHOLAR_ID', '').strip()
    if not scholar_id:
        config = (Path(__file__).resolve().parent.parent / '_config.yml').read_text(
            encoding='utf-8'
        )
        match = re.search(r'googlescholar\s*:.*[?&]user=([\w-]+)', config)
        if not match:
            raise ValueError('Set GOOGLE_SCHOLAR_ID or author.googlescholar in _config.yml')
        scholar_id = match.group(1)
    return scholar_id


def write_stats(author, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    shield_data = {
        'schemaVersion': 1,
        'label': 'citations',
        'message': str(author['citedby']),
        'cacheSeconds': 300,
    }
    for filename, data in [('gs_data.json', author),
                           ('gs_data_shieldsio.json', shield_data)]:
        (output_dir / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )


def write_site_snapshot(author, output_path):
    snapshot = {
        'citedby': author['citedby'],
        'updated': author['updated'],
        'publications': {
            key: {'num_citations': publication['num_citations']}
            for key, publication in author['publications'].items()
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )


if __name__ == '__main__':
    stats = fetch_stats(get_scholar_id())
    crawler_dir = Path(__file__).resolve().parent
    write_stats(stats, crawler_dir / 'results')
    write_site_snapshot(stats, crawler_dir.parent / '_data' / 'google_scholar_stats.json')
    print(f"Updated {stats['name']}: {stats['citedby']} citations ({stats['updated']})")
