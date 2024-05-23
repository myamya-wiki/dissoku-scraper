import cloudscraper # type: ignore
from bs4 import BeautifulSoup
import csv
import os
import logging

# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def ensure_directory_exists(filename):
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def scrape_urls_and_save_to_csv(base_url, page_url, filename):
    ensure_directory_exists(filename)
    page_number = 1
    scraper = cloudscraper.create_scraper()

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        while True:
            current_page = f"{page_url}{page_number}"
            try:
                response = scraper.get(current_page)
                if response.status_code != 200:
                    logging.error(f"Failed to get a proper response from {current_page}. Status code: {response.status_code}")
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                new_urls_found = False

                for link in links:
                    href = link['href']
                    if href.startswith(base_url):
                        writer.writerow([href])
                        new_urls_found = True

                if not new_urls_found:
                    print("No new URLs found. Ending scrape.")
                    break

                print(f"Saved: {current_page}")
                page_number += 1
            except Exception as e:
                logging.error(f"Error processing page: {current_page}. Error: {str(e)}")

def scrape_canonical_urls(input_file, output_file):
    ensure_directory_exists(output_file)
    scraper = cloudscraper.create_scraper()
    
    while True:
        urls_remaining = False
        temp_urls = []
        
        with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            for row in reader:
                temp_urls.append(row)

        if not temp_urls:
            print("No more URLs to process. Exiting.")
            break

        with open(input_file, mode='w', newline='', encoding='utf-8') as infile, \
             open(output_file, mode='a', newline='', encoding='utf-8') as outfile:
            reader_writer = csv.writer(infile)
            writer = csv.writer(outfile)

            for row in temp_urls:
                url = row[0]
                try:
                    response = scraper.get(url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        canonical_link = soup.find('link', rel='canonical')
                        if canonical_link and canonical_link.has_attr('href'): # type: ignore
                            canonical_url = canonical_link['href'] # type: ignore
                            writer.writerow([canonical_url])  # Write each canonical URL as it's found
                            print(f"Found canonical URL: {canonical_url}")
                        else:
                            reader_writer.writerow(row)  # Re-write URL back if no canonical found
                    else:
                        reader_writer.writerow(row)  # Re-write URL back if fetch failed
                except Exception as e:
                    logging.error(f"Error scraping {url}: {str(e)}")
                    reader_writer.writerow(row)  # Re-write URL back if an exception occurred

def main():
    BASE_URL = "https://app.dissoku.net/api/guilds/"
    PAGE_URL = "https://dissoku.net/ja/servers?page="
    SCRAPED_FILE = "data/scraped_urls.csv"
    CANONICAL_FILE = "data/canonical_urls.csv"

    print("Starting initial URL scrape...")
    scrape_urls_and_save_to_csv(BASE_URL, PAGE_URL, SCRAPED_FILE)
    print("Starting to scrape canonical URLs...")
    scrape_canonical_urls(SCRAPED_FILE, CANONICAL_FILE)
    print("Canonical URL scraping completed.")

if __name__ == "__main__":
    main()
