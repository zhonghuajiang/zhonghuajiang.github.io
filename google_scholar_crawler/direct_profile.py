"""Read citation counts from the public Google Scholar profile HTML."""
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def read_profile_page(scholar_id, start):
    query = urlencode({'user': scholar_id, 'hl': 'en', 'pagesize': 100, 'cstart': start})
    request = Request('https://scholar.google.com/citations?' + query)
    with urlopen(request, timeout=30) as response:
        return response.read()


def parse_profile_page(html, scholar_id):
    soup = BeautifulSoup(html, 'html.parser')
    name = soup.select_one('#gsc_prf_in')
    total = soup.select_one('#gsc_rsb_st .gsc_rsb_std')
    if name is None or total is None or not total.get_text(strip=True).replace(',', '').isdigit():
        raise ValueError('Google Scholar returned no valid profile/citation total')
    publications = {}
    for row in soup.select('#gsc_a_b .gsc_a_tr'):
        title = row.select_one('a.gsc_a_at')
        count = row.select_one('.gsc_a_ac')
        if title is None or count is None:
            raise ValueError('Incomplete publication row in Google Scholar response')
        pub_ids = parse_qs(urlparse(title.get('href', '')).query).get('citation_for_view', [])
        if not pub_ids or not pub_ids[0].startswith(scholar_id + ':'):
            raise ValueError('Unexpected publication ID in Google Scholar response')
        count_text = count.get_text(strip=True).replace(',', '').rstrip('*')
        if count_text and not count_text.isdigit():
            raise ValueError('Invalid publication citation count')
        publications[pub_ids[0]] = {
            'author_pub_id': pub_ids[0],
            'bib': {'title': title.get_text(strip=True)},
            'num_citations': int(count_text or '0'),
        }
    if not publications and soup.select_one('#gsc_a_b') is None:
        raise ValueError('Google Scholar returned no publication table')
    more = soup.select_one('#gsc_bpf_more')
    has_more = more is not None and not more.has_attr('disabled')
    return {
        'name': name.get_text(strip=True),
        'scholar_id': scholar_id,
        'citedby': int(total.get_text(strip=True).replace(',', '')),
        'publications': publications,
    }, has_more


def fetch_stats(scholar_id):
    author = None
    start = 0
    while True:
        print(f'Fetching public Google Scholar profile (start={start})', flush=True)
        page, has_more = parse_profile_page(read_profile_page(scholar_id, start), scholar_id)
        if author is None:
            author = page
        else:
            if not page['publications'] or set(page['publications']).issubset(author['publications']):
                raise ValueError('Google Scholar pagination did not advance')
            author['publications'].update(page['publications'])
        if not has_more:
            break
        start += 100
        if start >= 10000:
            raise ValueError('Google Scholar publication pagination limit exceeded')
    author['updated'] = datetime.now(timezone.utc).isoformat()
    return author
