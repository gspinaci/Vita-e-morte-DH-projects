import csv
import requests
import time
from datetime import datetime
import sys
import re
import logging
from urllib.parse import urlparse

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    green = Fore.GREEN
    blue = Fore.BLUE
    reset = Style.RESET_ALL
except ImportError:
    green = '\033[92m'
    blue = '\033[94m'
    reset = '\033[0m'

# Set up logging
logging.basicConfig(
    filename='script_final.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Constants
CDX_API_URL = "https://web.archive.org/cdx/search/cdx"
MAX_RETRIES = 10              # Fewer retries to avoid extreme backoff times
BACKOFF_FACTOR = 2           # Exponential backoff base
RATE_LIMIT_DELAY = 5         # ~15 requests/minute => 4 seconds each => ~18+ min for 280 URLs

def get_wayback_info(url):
    """
    Returns:
      (first_seen_dt, last_seen_dt, last_snapshot_link)
    for the URL from the Wayback Machine, considering ALL snapshots except 4xx and 5xx.
    We remove 'collapse' so we can see all timestamps, then manually filter.

    last_snapshot_link is the clickable Wayback link for the most recent snapshot.
    """

    # No filter for status code here; we retrieve everything, then filter out 4xx, 5xx in Python.
    params = {
        'url': url,
        'output': 'json',
        'fl': 'timestamp,original,statuscode',
        'limit': '100000',
        'matchType': 'prefix',  # Uncomment if you need to include domain variants
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logging.debug(f"[Wayback Attempt {attempt}] Requesting CDX API for URL: {url} | Params={params}")
            response = requests.get(CDX_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # data[0] = header row: ["timestamp","original","statuscode"]
            # data[1:] = actual snapshot records
            if len(data) < 2:
                logging.info(f"No timestamps returned for URL {url}. Data length: {len(data)}")
                return None, None, None

            rows = data[1:]
            if not rows:
                logging.info(f"No valid rows in the response for URL {url}")
                return None, None, None

            # Filter out 4xx/5xx snapshots
            valid_snapshots = []
            for row in rows:
                ts_str = row[0]   # "YYYYmmddHHMMSS"
                orig_url = row[1]
                code_str = row[2]
                try:
                    code_int = int(code_str)
                except ValueError:
                    # If for some reason code is non-numeric, skip
                    continue

                # Keep only if NOT in 400–599 range
                if 400 <= code_int < 600:
                    continue

                valid_snapshots.append((ts_str, orig_url, code_int))

            if not valid_snapshots:
                logging.info(f"After filtering out 4xx/5xx, no snapshots left for URL {url}")
                return None, None, None

            # Sort by timestamp ascending
            valid_snapshots.sort(key=lambda tup: tup[0])
            first_ts, first_orig, first_code = valid_snapshots[0]
            last_ts, last_orig, last_code = valid_snapshots[-1]

            first_seen_dt = datetime.strptime(first_ts, "%Y%m%d%H%M%S")
            last_seen_dt = datetime.strptime(last_ts, "%Y%m%d%H%M%S")

            # Build the clickable Wayback link for the last snapshot
            last_snapshot_link = f"https://web.archive.org/web/{last_ts}/{last_orig}"

            logging.debug(f"First seen: {first_seen_dt}, Last seen: {last_seen_dt} (code={last_code}), Link={last_snapshot_link}")
            return first_seen_dt, last_seen_dt, last_snapshot_link

        except requests.RequestException as e:
            logging.warning(f"RequestException on attempt {attempt} for URL {url}: {e}")
            if attempt == MAX_RETRIES:
                logging.error(f"Max retries exceeded for URL {url}")
                return None, None, None
            sleep_time = BACKOFF_FACTOR ** (attempt - 1)
            logging.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        except ValueError as e:
            logging.error(f"Error decoding JSON for URL {url}: {e}")
            return None, None, None
        except Exception as e:
            logging.error(f"Unexpected error for URL {url}: {e}")
            return None, None, None

def check_url_status(url):
    """
    Makes a standard GET request to check the *current* status code for the URL.
    """
    try:
        logging.debug(f"Checking URL status for {url}")
        response = requests.get(url, timeout=10)
        return response.status_code
    except requests.RequestException as e:
        logging.warning(f"Status check failed for {url}: {e}")
        return None

def is_valid_url(url):
    """
    Checks if the given string matches an http/https or www-based URL format.
    """
    if not url:
        return False
    pattern = re.compile(r'^(http(s)?://|www\.)[^\s]+$')
    return bool(pattern.match(url))

def normalize_url(url):
    """
    Ensures the URL has a scheme (http://) if missing, or if it starts with 'www.'
    """
    if url.startswith("www."):
        return "http://" + url
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        return "http://" + url
    return url

# Input/Output CSV files
input_csv = "lista_finale.csv"
output_csv = "lista_finale_post_script.csv"

# Read the input CSV
with open(input_csv, newline='', encoding='utf-8') as infile:
    first_line = infile.readline().strip('\n')
    fieldnames = [f.strip() for f in first_line.split(',')]
    infile.seek(0)
    reader = csv.DictReader(infile, fieldnames=fieldnames)
    rows = list(reader)

# If the first row is the header row, remove it from actual data
if rows and rows[0][fieldnames[0]] == fieldnames[0]:
    rows = rows[1:]

total_urls = len(rows)

if total_urls == 0:
    print("No URLs found in input file.")
    logging.info("No URLs found in input file.")
    sys.exit()

start_time = time.time()
running_time_sum = 0.0

# We add a new column: "URL progetto Last_URL_Snapshot"
# (Similarly for "URL sito vetrina Last_URL_Snapshot" if needed)
extra_fields = [
    "URL progetto First_Seen", 
    "URL progetto Last_Seen", 
    "URL progetto Status_Code",
    "URL progetto Last_URL_Snapshot",
    "URL sito vetrina First_Seen", 
    "URL sito vetrina Last_Seen", 
    "URL sito vetrina Status_Code",
    "URL sito vetrina Last_URL_Snapshot"
]

def process_url(url_value):
    """
    Checks if the URL is valid, normalizes it, queries Wayback for first/last seen,
    retrieves the last snapshot link, and does a live GET to retrieve current status code.
    """
    logging.debug(f"Processing URL: {url_value}")

    if not is_valid_url(url_value):
        logging.debug(f"URL is not valid or empty: {url_value}")
        return {
            "first_seen": "NOTPROVIDED",
            "last_seen": "NOTPROVIDED",
            "status_code": "NOTPROVIDED",
            "last_snapshot_link": ""
        }

    normalized_url = normalize_url(url_value)
    logging.debug(f"Normalized URL: {normalized_url}")

    # Current live status
    status_code = check_url_status(normalized_url)
    if status_code is None:
        status_code = "NOSTATUSCODE"

    # Wayback data
    first_dt, last_dt, last_url_snapshot = get_wayback_info(normalized_url)

    # Format the dates if they exist
    first_str = first_dt.strftime("%Y-%m-%d %H:%M:%S") if first_dt else ""
    last_str = last_dt.strftime("%Y-%m-%d %H:%M:%S") if last_dt else ""

    return {
        "first_seen": first_str,
        "last_seen": last_str,
        "status_code": status_code,
        "last_snapshot_link": last_url_snapshot or ""
    }

# Write to the output CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames + extra_fields)
    writer.writeheader()

    for i, row in enumerate(rows, start=1):
        iteration_start = time.time()

        url_progetto = row.get("URL progetto", "").strip()
        url_sito_vetrina = row.get("URL sito vetrina", "").strip()

        logging.debug(f"Row {i}: URL progetto: {url_progetto}, URL sito vetrina: {url_sito_vetrina}")

        # Process "URL progetto"
        progetto_info = process_url(url_progetto)
        # Process "URL sito vetrina"
        vetrina_info = process_url(url_sito_vetrina)

        # Update the row with new fields
        row["URL progetto First_Seen"] = progetto_info["first_seen"]
        row["URL progetto Last_Seen"] = progetto_info["last_seen"]
        row["URL progetto Status_Code"] = progetto_info["status_code"]
        row["URL progetto Last_URL_Snapshot"] = progetto_info["last_snapshot_link"]

        row["URL sito vetrina First_Seen"] = vetrina_info["first_seen"]
        row["URL sito vetrina Last_Seen"] = vetrina_info["last_seen"]
        row["URL sito vetrina Status_Code"] = vetrina_info["status_code"]
        row["URL sito vetrina Last_URL_Snapshot"] = vetrina_info["last_snapshot_link"]

        writer.writerow(row)

        # Rate limiting ( ~15 requests per minute = 4s delay )
        time.sleep(RATE_LIMIT_DELAY)

        # Progress bar / time estimation
        iteration_time = time.time() - iteration_start
        running_time_sum += iteration_time
        elapsed = time.time() - start_time

        avg_time_per_url = running_time_sum / i
        estimated_total = avg_time_per_url * total_urls
        estimated_remaining = estimated_total - elapsed

        progress_percentage = (i / total_urls) * 100
        progress_bar_width = 50
        filled_length = int(progress_bar_width * i / total_urls)
        bar = '#' * filled_length + '-' * (progress_bar_width - filled_length)

        sys.stdout.write("\033[K")  # Clear line
        sys.stdout.write(
            f"\r{blue}[{bar}] {progress_percentage:.1f}% done | "
            f"Estimated remaining: ~{estimated_remaining:.1f}s ({estimated_remaining/60:.1f}m){reset}"
        )
        sys.stdout.flush()

end_time = time.time()
total_elapsed = end_time - start_time
print("\n" + green + f"Done. Time elapsed: {total_elapsed:.2f} seconds." + reset)
logging.info(f"Processing complete. Time elapsed: {total_elapsed:.2f} seconds.")
