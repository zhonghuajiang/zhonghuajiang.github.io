import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import main
import direct_profile

PROFILE = """<div id="gsc_prf_in">Test Author</div>
<table id="gsc_rsb_st"><tr><td class="gsc_rsb_std">0</td></tr></table>
<table><tbody id="gsc_a_b"><tr class="gsc_a_tr">
<td><a class="gsc_a_at" href="/citations?citation_for_view=author:paper">Paper</a></td>
<td><a class="gsc_a_ac"></a></td></tr></tbody></table>
<button id="gsc_bpf_more" disabled></button>"""


class ScholarStatsTests(unittest.TestCase):
    def test_id_falls_back_to_site_profile(self):
        with patch.dict(os.environ, {'GOOGLE_SCHOLAR_ID': ''}):
            self.assertEqual(main.get_scholar_id(), 'VsZaHKIAAAAJ')

    def test_secret_overrides_site_profile(self):
        with patch.dict(os.environ, {'GOOGLE_SCHOLAR_ID': ' override-id '}):
            self.assertEqual(main.get_scholar_id(), 'override-id')

    def test_fetch_and_write_preserve_publication_keys_and_zero_citations(self):
        with patch.object(direct_profile, 'read_profile_page', return_value=PROFILE):
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
        for html in ['<html>captcha</html>', PROFILE.replace('>0</td>', '>invalid</td>'),
                     PROFILE.replace('author:paper', 'other:paper')]:
            with self.subTest(html=html), \
                 patch.object(direct_profile, 'read_profile_page', return_value=html):
                with self.assertRaises(ValueError):
                    main.fetch_stats('author')

    def test_pagination_collects_all_publications(self):
        first = PROFILE.replace('disabled', '')
        second = PROFILE.replace('author:paper', 'author:second')
        with patch.object(direct_profile, 'read_profile_page', side_effect=[first, second]) as read:
            data = main.fetch_stats('author')
        self.assertEqual(set(data['publications']), {'author:paper', 'author:second'})
        self.assertEqual(read.call_args_list[1].args, ('author', 100))

    def test_repeated_pagination_is_rejected(self):
        with patch.object(direct_profile, 'read_profile_page', return_value=PROFILE.replace('disabled', '')):
            with self.assertRaisesRegex(ValueError, 'pagination did not advance'):
                main.fetch_stats('author')

    def test_forbidden_response_reports_required_network_change(self):
        error = HTTPError('https://scholar.google.com/citations', 403, 'Forbidden', {}, None)
        with patch.object(direct_profile, 'urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'HTTP 403'):
                main.fetch_stats('author')


if __name__ == '__main__':
    unittest.main()
