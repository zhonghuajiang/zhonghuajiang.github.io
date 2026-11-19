import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class ScholarStatsTests(unittest.TestCase):
    def test_id_falls_back_to_site_profile(self):
        with patch.dict(os.environ, {'GOOGLE_SCHOLAR_ID': ''}):
            self.assertEqual(main.get_scholar_id(), 'VsZaHKIAAAAJ')

    def test_secret_overrides_site_profile(self):
        with patch.dict(os.environ, {'GOOGLE_SCHOLAR_ID': ' override-id '}):
            self.assertEqual(main.get_scholar_id(), 'override-id')

    def test_fetch_and_write_preserve_publication_keys_and_zero_citations(self):
        author = {'name': 'Test Author', 'citedby': 0, 'publications': [
            {'author_pub_id': 'author:paper', 'num_citations': 0}
        ]}
        with patch.object(main.scholarly, 'search_author_id', return_value=author), \
             patch.object(main.scholarly, 'fill'):
            data = main.fetch_stats('author')
        self.assertEqual(data['publications']['author:paper']['num_citations'], 0)
        self.assertTrue(data['updated'].endswith('+00:00'))
        with tempfile.TemporaryDirectory() as directory:
            main.write_stats(data, Path(directory))
            main.write_site_snapshot(data, Path(directory) / 'snapshot.json')
            snapshot = json.loads((Path(directory) / 'snapshot.json').read_text(encoding='utf-8'))
            self.assertEqual(snapshot['citedby'], 0)
            self.assertEqual(snapshot['publications']['author:paper']['num_citations'], 0)
            stats = json.loads((Path(directory) / 'gs_data.json').read_text(encoding='utf-8'))
            badge = json.loads((Path(directory) / 'gs_data_shieldsio.json').read_text(encoding='utf-8'))
        self.assertEqual(stats['citedby'], 0)
        self.assertEqual(badge['message'], '0')

    def test_incomplete_crawl_is_rejected(self):
        for author in [{'publications': []}, {'citedby': -1, 'publications': []}, {'citedby': 12}]:
            with self.subTest(author=author), \
                 patch.object(main.scholarly, 'search_author_id', return_value=author), \
                 patch.object(main.scholarly, 'fill'):
                with self.assertRaises(ValueError):
                    main.fetch_stats('author')


if __name__ == '__main__':
    unittest.main()
