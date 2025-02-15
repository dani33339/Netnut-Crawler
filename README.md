# Netnut Crawler

## Overview
Netnut Crawler is a Python-based web scraper designed to interact with the [NetNut SERP Scraper API](https://netnut.io/serp-scraper-api/). The crawler leverages proxy usage to bypass CAPTCHA challenges that appear after multiple retries from the same IP address.

## Features
- **Access Key Extraction**: Retrieves client-specific `client_id` and `client_secret` required to access the SERP Scraper API.
- **Proxy Management**: Utilizes proxies to avoid detection and bypass CAPTCHA restrictions.
- **Retry Mechanism**: Implements automatic retries in case of failures or blocked requests.
- **Threading Logic**: Uses multi-threading to efficiently handle multiple requests concurrently.
- **Locks and Synchronization**: Ensures thread safety using locks to prevent resource conflicts.
- **Proxy Ban Handling**: Detects and switches proxies when an IP gets banned.

## How It Works
1. Extracts access keys (`client_id`, `client_secret`) from NetNut's JavaScript files to authenticate API requests.
1. Sends requests to the NetNut SERP Scraper API.
2. Detects failed requests due to CAPTCHA or bans.
3. Automatically retries with a different proxy upon failure.
4. Uses threading to speed up the crawling process while maintaining efficiency.
5. Implements locks to ensure smooth execution in a multi-threaded environment.


## Development Process
This project required extensive planning, research, and debugging:
- **Planning**: Defined goals, API structure, and proxy management strategies.
- **Inspection**: Analyzed NetNut's API responses, authentication mechanisms, and CAPTCHA triggers.
- **Research**: Explored multi-threading, proxy rotation, and lock mechanisms for concurrency control.
- **Implementation**: Developed the crawler with error handling, retries, and proxy rotation.
- **Testing & Optimization**: Debugged performance bottlenecks and fine-tuned proxy management.

## Proxy Configuration
- The crawler requires a list of proxies to function correctly. These proxies help avoid detection and CAPTCHA challenges.

- The proxies.txt file should contain one proxy per line in the following format:
```sh
Username:Password@Address:Port
Username:Password@Address:Port
Username:Password@Address:Port
```
- The project has been tested with 50 requests on 40 threads using 10 proxies to optimize performance and reliability.

## Requirements
- Python 3.x
- Required dependencies (specified in `requirements.txt`)
- proxies.txt file with working proxies

## Installation
```sh
# Clone the repository
git clone https://github.com/dani33339/Netnut-Crawler.git

# Navigate to the project directory
cd Netnut-Crawler

# Install dependencies
pip install -r requirements.txt
```

## Usage
```sh
python main.py
```


