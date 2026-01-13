"""
Benchmark script to measure Kanbanize sync performance.
Runs summary fetch (pages) with different `per_page` and detail fetch concurrently with different worker counts.
Defaults to board_id = 75.

Usage: python3 scripts/test_sync_perf.py
"""

import sys
import time
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from integrations.kanbanize import KanbanizeAPI
import concurrent.futures

BOARD_ID = 75
PER_PAGE_LIST = [50, 100, 200]
WORKERS_LIST = [10, 20, 40]


def fetch_summaries(api, board_id, per_page, max_pages=1000):
    """Fetch card summaries (cards list) paging until empty batch. Returns list of card_ids and elapsed time."""
    start = time.time()
    card_ids = []
    page = 1
    total_fetched = 0
    while True:
        res = api.buscar_cards_simples(board_ids=[board_id], page=page, per_page=per_page)
        if not res.get('sucesso'):
            raise RuntimeError(f"Error fetching summaries: {res}")
        batch = res.get('dados', [])
        if not batch:
            break
        for item in batch:
            # item may already contain card_id or nested 'card_id'
            cid = item.get('card_id') if isinstance(item, dict) else None
            if cid is not None:
                card_ids.append(cid)
        total_fetched += len(batch)
        page += 1
        if page > max_pages:
            break
    elapsed = time.time() - start
    return card_ids, elapsed, total_fetched


def fetch_details(api, card_ids, workers):
    """Fetch card details concurrently using buscar_detalhe_unico."""
    start = time.time()
    details = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(api.buscar_detalhe_unico, cid): cid for cid in card_ids}
        for fut in concurrent.futures.as_completed(futures):
            try:
                res = fut.result()
                if res.get('sucesso'):
                    details.append(res.get('dados'))
                else:
                    details.append(None)
            except Exception:
                details.append(None)
    elapsed = time.time() - start
    return details, elapsed


def run_benchmark(board_id=BOARD_ID):
    if not settings.KANBANIZE_ENABLED:
        print('Kanbanize not enabled in settings')
        return
    api = KanbanizeAPI(settings.KANBANIZE_BASE_URL, settings.KANBANIZE_API_KEY)

    results = []
    for per_page in PER_PAGE_LIST:
        print('\n=== Testing per_page =', per_page, '===')
        # fetch summaries
        card_ids, t_summary, total = fetch_summaries(api, board_id, per_page)
        print(f'Summaries fetched: {total} ids in {t_summary:.2f}s (per_page={per_page})')

        # for each workers setting, fetch details
        for workers in WORKERS_LIST:
            print(f' -> Fetching details with {workers} workers...')
            details, t_details = fetch_details(api, card_ids, workers)
            total_time = t_summary + t_details
            print(f'    Details: {len(details)} fetched in {t_details:.2f}s | total {total_time:.2f}s')
            results.append({
                'per_page': per_page,
                'workers': workers,
                'summary_time': t_summary,
                'details_time': t_details,
                'total_time': total_time,
                'count': len(details)
            })
    # Print summary table
    print('\n=== Results summary ===')
    for r in results:
        print(f"per_page={r['per_page']:3d} workers={r['workers']:2d} -> total={r['total_time']:.2f}s (summary={r['summary_time']:.2f}s details={r['details_time']:.2f}s) count={r['count']}")

    # Best config
    best = min(results, key=lambda x: x['total_time'])
    print('\nBest config:', best)


if __name__ == '__main__':
    start = time.time()
    try:
        run_benchmark()
    except Exception as e:
        print('Error during benchmark:', e)
    finally:
        print('\nBenchmark finished in {:.2f}s'.format(time.time() - start))
