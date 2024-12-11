import csv
import requests
import time
from datetime import datetime
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    green = Fore.GREEN
    blue = Fore.BLUE
    reset = Style.RESET_ALL
except ImportError:
    # Fallback to ANSI codes if colorama is not installed
    green = '\033[92m'
    blue = '\033[94m'
    reset = '\033[0m'

def get_wayback_info(url):
    cdx_url = "http://web.archive.org/cdx/search/cdx"
    params = {
        'url': url,
        'output': 'json',
        'fl': 'timestamp',
        'collapse': 'timestamp:8'
    }
    
    try:
        response = requests.get(cdx_url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None, None

    data = response.json()
    if len(data) < 2:
        return None, None

    timestamps = [row[0] for row in data[1:]]
    timestamps.sort()
    first_seen = timestamps[0]
    last_seen = timestamps[-1]

    first_seen_dt = datetime.strptime(first_seen, "%Y%m%d%H%M%S")
    last_seen_dt = datetime.strptime(last_seen, "%Y%m%d%H%M%S")

    return first_seen_dt, last_seen_dt

def check_url_status(url):
    try:
        r = requests.get(url, timeout=10)
        return r.status_code
    except requests.RequestException:
        return None

input_csv = "urls.csv"
output_csv = "url_status_archive.csv"

start_time = time.time()
processing_times = []
total_urls = 0

# Count total URLs in advance for estimation
with open(input_csv, newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    urls = [row[0].strip() for row in reader if row and row[0].strip()]
    total_urls = len(urls)

if total_urls == 0:
    print("No URLs found in input file.")
    exit()

with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(["URL", "Status_Code", "First_Seen", "Last_Seen"])

    for i, url in enumerate(urls, start=1):
        iteration_start = time.time()

        # Check status
        status_code = check_url_status(url)

        # Get Wayback info
        first_seen_dt, last_seen_dt = get_wayback_info(url)

        first_seen_str = first_seen_dt.strftime("%Y-%m-%d %H:%M:%S") if first_seen_dt else ""
        last_seen_str = last_seen_dt.strftime("%Y-%m-%d %H:%M:%S") if last_seen_dt else ""

        writer.writerow([url, status_code, first_seen_str, last_seen_str])

        # Clear the previous estimated time line
        sys.stdout.write("\033[K")  # ANSI escape sequence to clear the line
        sys.stdout.write(f"\r")  # Return carriage to the start of the line

        # Print status info
        print(f"Checked URL #{i}/{total_urls}: {url}")
        print(f"  Status Code: {status_code}")
        if first_seen_str or last_seen_str:
            print(f"  First Seen: {first_seen_str}, Last Seen: {last_seen_str}")
        else:
            print("  No Wayback snapshots found.")
        
        # Time tracking
        iteration_time = time.time() - iteration_start
        if i <= 3:
            processing_times.append(iteration_time)

        # After the first 3 URLs, estimate completion time
        if i >= 3 and len(processing_times) >= 3:
            avg_time_per_url = sum(processing_times) / len(processing_times)
            remaining = total_urls - i
            estimated_total = (avg_time_per_url * total_urls)
            estimated_remaining = estimated_total - (time.time() - start_time)
            
            # Print estimated time in blue, overwriting the same line
            sys.stdout.write(f"\r{blue}Estimated time to completion: ~{estimated_remaining:.2f} seconds (~{estimated_remaining/60:.1f} minutes) remaining.{reset}")
            sys.stdout.flush()

# Final message
end_time = time.time()
elapsed = end_time - start_time
print("\n" + green + f"Done. Time elapsed: {elapsed:.2f} seconds." + reset)
