import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from proxy_manager import ProxyManager
from scraper import get_serp_results

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    proxy_manager = ProxyManager()
    if not proxy_manager.read_proxies("proxies.txt"):
        logging.error("No proxies loaded. Exiting.")
        return

    search_terms = [f"nana{_}" for _ in range(50)]

    # Dynamically determine the thread pool size based on available CPU cores
    cpu_count = multiprocessing.cpu_count()
    max_threads = max(10, (cpu_count * 5) // 2)

    logging.info(f"Using a thread pool with {max_threads} threads.")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(lambda term: get_serp_results(term, proxy_manager), search_terms)


if __name__ == "__main__":
    main()
