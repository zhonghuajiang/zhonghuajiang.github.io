"""Fetch fresh citations locally and publish only the citation data branch."""
import subprocess
import tempfile
from pathlib import Path

from main import fetch_stats, get_scholar_id, write_stats


ROOT = Path(__file__).resolve().parent.parent


def git(*args, cwd=ROOT, check=True):
    return subprocess.run(['git', *args], cwd=cwd, check=check)


def publish(results):
    git('fetch', 'origin', 'google-scholar-stats')
    with tempfile.TemporaryDirectory(prefix='scholar-publish-') as directory:
        temporary_root = Path(directory).resolve()
        worktree = (temporary_root / 'stats').resolve()
        if not worktree.is_relative_to(temporary_root):
            raise ValueError('Publication worktree must be inside its temporary directory')
        git('worktree', 'add', '--detach', str(worktree), 'FETCH_HEAD')
        try:
            for name in ['gs_data.json', 'gs_data_shieldsio.json']:
                (worktree / name).write_bytes((results / name).read_bytes())
            git('add', 'gs_data.json', 'gs_data_shieldsio.json', cwd=worktree)
            changed = git('diff', '--cached', '--quiet', cwd=worktree, check=False)
            if changed.returncode == 0:
                print('Citation data is already up to date.')
                return
            if changed.returncode != 1:
                changed.check_returncode()
            git('commit', '-m', 'Update Google Scholar citation data', cwd=worktree)
            git('push', 'origin', 'HEAD:google-scholar-stats', cwd=worktree)
        finally:
            git('worktree', 'remove', str(worktree))


if __name__ == '__main__':
    stats = fetch_stats(get_scholar_id())
    results = ROOT / 'google_scholar_crawler' / 'results'
    write_stats(stats, results)
    publish(results)
    print(f"Published {stats['citedby']} citations, fetched at {stats['updated']}")
