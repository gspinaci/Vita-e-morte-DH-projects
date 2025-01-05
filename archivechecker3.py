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
MAX_RETRIES = 8
BACKOFF_FACTOR = 4
RATE_LIMIT_DELAY = 6  # Delay in seconds to maintain ~15 requests per minute

def get_wayback_info(url):
    """
    Returns (first_seen_datetime, last_seen_datetime) for the URL from the Wayback Machine
    by querying only statuscode=200 snapshots (removing daily collapse).
    """
    # Updated parameters: remove collapse, add filter=statuscode:200, add limit=5000
    params = {
        'url': url,
        'output': 'json',
        'fl': 'timestamp,original,statuscode',
        'filter': 'statuscode:200',
        'limit': '5000',
        # 'matchType': 'prefix',  # Uncomment if you need to capture domain variants (e.g., http vs. https)
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logging.debug(f"Attempt {attempt}: Requesting CDX API for URL: {url} with params: {params}")
            response = requests.get(CDX_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.debug(f"CDX API JSON for {url}: {data}")

            # data[0] is the header row (e.g. ["timestamp","original","statuscode"])
            # data[1:] are the actual snapshot records
            if len(data) < 2:
                logging.info(f"No timestamps returned for URL {url}. Data length: {len(data)}")
                return None, None

            rows = data[1:]  # skip the header
            if not rows:
                logging.info(f"No valid rows in the response for {url}")
                return None, None

            # row[0] = timestamp, row[1] = original, row[2] = statuscode
            timestamps = [row[0] for row in rows]
            timestamps.sort()
            if not timestamps:
                logging.info(f"No timestamps in parsed data for URL {url}")
                return None, None

            first_seen = timestamps[0]
            last_seen = timestamps[-1]

            first_seen_dt = datetime.strptime(first_seen, "%Y%m%d%H%M%S")
            last_seen_dt = datetime.strptime(last_seen, "%Y%m%d%H%M%S")

            logging.debug(f"First seen: {first_seen_dt}, Last seen: {last_seen_dt} for URL {url}")
            return first_seen_dt, last_seen_dt

        except requests.RequestException as e:
            logging.warning(f"RequestException on attempt {attempt} for URL {url}: {e}")
            if attempt == MAX_RETRIES:
                logging.error(f"Max retries exceeded for URL {url}")
                return None, None
            sleep_time = BACKOFF_FACTOR ** (attempt - 1)
            logging.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        except ValueError as e:
            logging.error(f"Error decoding JSON for URL {url}: {e}")
            return None, None
        except Exception as e:
            logging.error(f"Unexpected error for URL {url}: {e}")
            return None, None

def check_url_status(url):
    """
    Makes a standard GET request to check the current status code for the URL.
    """
    try:
        logging.debug(f"Checking URL status for {url}")
        response = requests.get(url, timeout=10)
        logging.debug(f"Status code for {url}: {response.status_code}")
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

extra_fields = [
    "URL progetto First_Seen", 
    "URL progetto Last_Seen", 
    "URL progetto Status_Code",
    "URL sito vetrina First_Seen", 
    "URL sito vetrina Last_Seen", 
    "URL sito vetrina Status_Code"
]

def process_url(url_value):
    """
    Checks if the URL is valid, normalizes it, hits the CDX API to get first/last seen,
    and does a direct GET request to retrieve the current status code.
    """
    logging.debug(f"Processing URL: {url_value}")

    if not is_valid_url(url_value):
        logging.debug(f"URL is not valid or empty: {url_value}")
        return "NOTPROVIDED", "NOTPROVIDED", "NOTPROVIDED"

    normalized_url = normalize_url(url_value)
    logging.debug(f"Normalized URL: {normalized_url}")

    status_code = check_url_status(normalized_url)
    first_seen_dt, last_seen_dt = get_wayback_info(normalized_url)

    first_seen_str = first_seen_dt.strftime("%Y-%m-%d %H:%M:%S") if first_seen_dt else ""
    last_seen_str = last_seen_dt.strftime("%Y-%m-%d %H:%M:%S") if last_seen_dt else ""

    if not first_seen_dt or not last_seen_dt:
        logging.debug(f"No valid Wayback timestamps found for {normalized_url}")

    if status_code is None:
        status_code = "NOSTATUSCODE"

    return first_seen_str, last_seen_str, status_code

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
        progetto_first_seen, progetto_last_seen, progetto_status = process_url(url_progetto)

        # Process "URL sito vetrina" if needed
        # (Currently commented out in your original script)
        # vetrina_first_seen, vetrina_last_seen, vetrina_status = process_url(url_sito_vetrina)
        vetrina_first_seen = ""
        vetrina_last_seen = ""
        vetrina_status = ""

        # Update the row with new fields
        row["URL progetto First_Seen"] = progetto_first_seen
        row["URL progetto Last_Seen"] = progetto_last_seen
        row["URL progetto Status_Code"] = progetto_status

        row["URL sito vetrina First_Seen"] = vetrina_first_seen
        row["URL sito vetrina Last_Seen"] = vetrina_last_seen
        row["URL sito vetrina Status_Code"] = vetrina_status

        writer.writerow(row)

        # Rate limiting to avoid hitting Wayback Machine too fast
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
            f"\r{blue}[{bar}] {progress_percentage:.1f}% done | Estimated remaining: ~{estimated_remaining:.1f}s "
            f"({estimated_remaining/60:.1f}m){reset}"
        )
        sys.stdout.flush()

end_time = time.time()
total_elapsed = end_time - start_time
print("\n" + green + f"Done. Time elapsed: {total_elapsed:.2f} seconds." + reset)
logging.info(f"Processing complete. Time elapsed: {total_elapsed:.2f} seconds.")
