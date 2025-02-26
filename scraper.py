import json
import requests
import re
from fake_useragent import UserAgent
import logging
from functools import wraps
from datetime import datetime

ua = UserAgent()


class RetryTracker:
    """
    Tracks failed search attempts, storing the attempt number, timestamp, and error message.
    """

    def __init__(self):
        self.failed_searches = {}

    def record_failure(self, search_value, attempt, error):
        """
        Records a failed search attempt.

        :param search_value: The search query attempted
        :param attempt: The attempt number
        :param error: The exception that occurred
        """
        if search_value not in self.failed_searches:
            self.failed_searches[search_value] = []

        self.failed_searches[search_value].append({
            'attempt': attempt,
            'timestamp': datetime.now(),
            'error': str(error)
        })

    def get_failure_report(self):
        """
        Returns the dictionary of failed searches.
        """
        return self.failed_searches


def retry_with_tracking(tries=10):
    """
    Decorator that retries a function up to a specified number of times and tracks failures.

    :param tries: Maximum number of retry attempts (set to 10 as number of proxies I used is 10)
    """
    retry_tracker = RetryTracker()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(tries + 1):  # Allow one original call + 10 retries
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    search_value = args[0] if args else kwargs.get('search_value')
                    retry_tracker.record_failure(search_value, attempt + 1, e)

                    if attempt == tries:  # Last attempt (after all retries)
                        logging.error(f"All {tries + 1} attempts failed for search '{search_value}'")
                        logging.error("Failure history:")
                        for failure in retry_tracker.failed_searches[search_value]:
                            logging.error(f"Attempt {failure['attempt']}: {failure['error']} at {failure['timestamp']}")
                        raise  # Re-raise the last exception

                    logging.warning(f"Attempt {attempt + 1}/{tries + 1} failed for '{search_value}'. Retrying...")

        return wrapper

    return decorator


def get_access_keys(proxy):
    """
    Extracts access keys from netnut api using a given proxy.

    :param proxy: The proxy to use for the request
    :return: A tuple containing (client_id, client_secret) if found, otherwise raises an error
    """
    url = "https://playground.netnut.io/_next/static/chunks/5396-fb805b9d40b0a4c9.js"

    headers = {
        'Referer': 'https://playground.netnut.io/playground/',
        'User-Agent': ua.random,
    }

    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=5)
        data = response.text

        client_id_match = re.search(r'CF_ACCESS_CLIENT_ID:\s*"([^"]+)"', data)
        client_secret_match = re.search(r'CF_ACCESS_CLIENT_SECRET:\s*"([^"]+)"', data)

        if client_id_match and client_secret_match:
            return client_id_match.group(1), client_secret_match.group(1)
        else:
            logging.warning(f"Keys not found for proxy: {proxy}. Retrying...")
            raise ValueError(f"Access keys not found for proxy: {proxy}")

    except requests.RequestException as e:
        logging.error(f"get_access_keys request failed for proxy {proxy}: {e}")
        raise


@retry_with_tracking(tries=10)
def get_serp_results(search_value, proxy_manager):
    """
    Performs a search request using the obtained access keys and a shared proxy.

    :param search_value: The search query to be executed
    :param proxy_manager: An instance of a proxy manager handling proxies
    :return: None (results are saved to a file)
    """
    proxy, proxy_key = proxy_manager.get_proxy()

    client_id, client_secret = get_access_keys(proxy)
    if not client_id or not client_secret:
        raise ValueError(f"Failed to retrieve access keys for proxy: {proxy_key}")  # Trigger retry

    url = "https://netnut-api.netnut.io/api/v1/playground/search"

    payload = json.dumps({
        "googleDomain": "www.google.com",
        "gl": "us",
        "hl": "en",
        "uule": "w+CAIQICIeTmFudGVzLFBheXMgZGUgbGEgTG9pcmUsRnJhbmNl",
        "q": search_value,
        "start": 0,
        "sum": 10,
        "safe": True,
        "filter": False,
        "nfpr": False,
        "captchaToken": "",
        "device": "desktop"
    })

    headers = {
        'accept': 'application/json, text/plain, */*',
        'cf-access-client-id': client_id,
        'cf-access-client-secret': client_secret,
        'content-type': 'application/json',
        'origin': 'https://playground.netnut.io',
        'referer': 'https://playground.netnut.io/',
        'user-agent': ua.random
    }

    response = requests.post(url, headers=headers, data=payload, proxies=proxy, timeout=5)

    # Ensure response is valid JSON (no captcha message)
    json_response = response.json()
    if not isinstance(json_response, dict):
        proxy_manager.ban_proxy(proxy_key)  # Ban failed proxy
        raise ValueError("Unexpected response format, retrying...")

    # Save the response to a file
    filename = f"{search_value}.txt"
    with open(filename, "w") as file:
        json.dump(json_response, file, indent=4)
    logging.info(f"Saved results to {filename} using proxy: {proxy_key}")

    proxy_manager.update_proxy(proxy_key)
