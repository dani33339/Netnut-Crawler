import time
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ua = UserAgent()


class ProxyManager:
    def __init__(self):
        """
        Initializes the ProxyManager with threading lock, proxy storage, and banned proxy tracking.
        """
        self.lock = threading.Lock()
        self.proxies = {}  # Stores proxies and their last used timestamps
        self.banned_proxies = {}  # Stores banned proxies with unban timestamps

    def read_proxies(self, file_name="proxies.txt"):
        """
        Reads proxies from a file and initializes the proxy list.

        :param file_name: Name of the file containing proxies.
        :return: True if proxies were loaded, False otherwise.
        """
        try:
            with open(file_name, "r") as f:
                self.proxies = {line.strip(): 0 for line in f if line.strip()}

            if not self.proxies:
                logging.error("No proxies loaded from file.")
                return False

            logging.info(f"Loaded {len(self.proxies)} proxies from {file_name}.")
            return True

        except FileNotFoundError:
            logging.error(f"Proxies file '{file_name}' not found.")
            return False

    def get_dynamic_delay(self):
        """
        Calculates the minimum wait time for a proxy to be unbanned.

        :return: Time in seconds until the soonest proxy is unbanned.
        """
        if not self.banned_proxies:
            return 0

        min_unban_time = min(self.banned_proxies.values())
        delay = max(0, min_unban_time - time.time())  # Time until the soonest proxy is unbanned
        return delay

    def dynamic_retry_decorator(func):
        """
        Decorator to retry a function with a dynamically calculated delay between attempts.

        :param func: Function to be decorated.
        :return: Wrapped function with retry logic.
        """

        def wrapper(self, *args, **kwargs):
            max_tries = 3
            tries = 0

            while tries < max_tries:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    tries += 1
                    if tries == max_tries:
                        raise e

                    # Recalculate delay time for each retry
                    delay = self.get_dynamic_delay()
                    logging.info(f"Attempt {tries} failed. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)

        return wrapper

    @dynamic_retry_decorator
    def get_proxy(self):
        """
        Selects the Least Recently Used (LRU) proxy that is not banned.

        :return: A dictionary containing the selected proxy and its key.
        """
        with self.lock:
            available_proxies = {
                proxy: last_used
                for proxy, last_used in self.proxies.items()
                if proxy not in self.banned_proxies or time.time() > self.banned_proxies[proxy]
            }

            if not available_proxies:
                delay = self.get_dynamic_delay()
                logging.error(f"No available proxies. Retrying in {delay:.2f} seconds...")
                raise ValueError("No available proxies, retrying...")

            least_used_proxy = min(available_proxies, key=available_proxies.get)
            self.proxies[least_used_proxy] = time.time()  # Update last used time

            return {
                "http": f"http://{least_used_proxy}",
                "https": f"http://{least_used_proxy}"
            }, least_used_proxy

    def update_proxy(self, proxy):
        """
        Updates the last-used timestamp for a given proxy.

        :param proxy: The proxy to update.
        """
        with self.lock:
            if proxy in self.proxies:
                self.proxies[proxy] = time.time()
                logging.info(f"Updated proxy usage: {proxy}")

    def ban_proxy(self, proxy):
        """
        Temporarily bans a failing proxy for 3 minutes.

        :param proxy: The proxy to be banned.
        """
        with self.lock:
            ban_time = time.time() + 180  # 3 minutes cooldown
            self.banned_proxies[proxy] = ban_time
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ban_time))
            logging.warning(f"Proxy {proxy} banned until {formatted_time} due to failure.")
