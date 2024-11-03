from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import time
from datetime import datetime
import os
from retrying import retry
from tqdm import tqdm


class AKCScraper:
    def __init__(self):
        self.base_url = "https://www.akc.org/dog-breeds/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)

        # Setup Chrome options
        self.chrome_options = Options()
        # self.chrome_options.add_argument('--headless')  # Comment this out for debugging
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument(
            f'user-agent={self.headers["User-Agent"]}')

        # Setup Chrome service
        self.service = Service(ChromeDriverManager().install())

    def get_breed_links(self):
        breeds = []
        driver = webdriver.Chrome(
            service=self.service, options=self.chrome_options)

        try:
            print("Starting to collect breed links...")
            alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

            for letter in alphabet:
                letter_url = f"{self.base_url}?letter={letter}"
                print(f"\nProcessing letter {letter} at URL: {letter_url}")

                # Initialize page counter
                page = 1
                has_more_pages = True
                retry_count = 0
                max_retries = 3

                while has_more_pages:
                    current_url = f"{self.base_url}page/{page}/?letter={letter}" if page > 1 else letter_url
                    print(f"Processing page {page} at {current_url}")

                    driver.get(current_url)

                    # Wait for the breed cards to load
                    try:
                        # First wait for the grid container
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, "breed-card-type-grid"))
                        )

                        # Then get all breed cards
                        breed_cards = driver.find_elements(
                            By.CSS_SELECTOR, ".breed-card-type-grid .grid-col")
                        num_breeds = len(breed_cards)

                        # If no breeds found, retry a few times
                        if num_breeds == 0:
                            retry_count += 1
                            if retry_count <= max_retries:
                                print(
                                    f"No breeds found, retrying... (Attempt {retry_count}/{max_retries})")
                                time.sleep(3)  # Wait a bit longer before retry
                                continue
                            else:
                                print(
                                    f"Failed to find breeds for letter {letter} after {max_retries} attempts")
                                break

                        print(f"Found {num_breeds} breeds on page {page}")

                        # Process breed cards
                        for card in breed_cards:
                            try:
                                link = card.find_element(By.TAG_NAME, 'a')
                                breed_info = {
                                    'name': link.text.strip(),
                                    'url': link.get_attribute('href')
                                }
                                # Avoid duplicates
                                if breed_info['url'] not in [b['url'] for b in breeds]:
                                    breeds.append(breed_info)
                                    print(f"Added breed: {breed_info['name']}")
                            except Exception as e:
                                print(f"Error processing card: {str(e)}")

                        # Reset retry count after successful processing
                        retry_count = 0

                        # If we found exactly 12 breeds, there's likely another page
                        has_more_pages = (num_breeds == 12)
                        if has_more_pages:
                            page += 1

                    except Exception as e:
                        print(
                            f"Error on page {page} for letter {letter}: {str(e)}")
                        retry_count += 1
                        if retry_count <= max_retries:
                            print(
                                f"Retrying... (Attempt {retry_count}/{max_retries})")
                            time.sleep(3)
                            continue
                        else:
                            print(
                                f"Failed after {max_retries} attempts, moving to next letter")
                            break

                    time.sleep(2)  # Be nice to the server

        except Exception as e:
            print(f"Error in get_breed_links: {str(e)}")

        finally:
            driver.quit()

        print(f"\nSuccessfully extracted {len(breeds)} breed links")
        return breeds

    def save_data(self, data):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save as JSON
        json_path = os.path.join(
            self.output_dir, f'dog_breeds_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"URLs saved to {json_path}")

    def scrape_all_breeds(self):
        breeds = self.get_breed_links()
        all_breeds_data = []

        for breed in tqdm(breeds, desc="Scraping breeds"):
            details = self.get_breed_details(breed['url'])
            if details:
                all_breeds_data.append(details)
            time.sleep(2)

        return all_breeds_data


def main():
    scraper = AKCScraper()
    print("Starting AKC breed URL collection...")
    breed_links = scraper.get_breed_links()
    scraper.save_data(breed_links)
    print("URL collection complete!")


if __name__ == "__main__":
    main()
