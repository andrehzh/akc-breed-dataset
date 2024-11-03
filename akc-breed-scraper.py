import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
import os


class AKCScraper:
    def __init__(self):
        self.base_url = "https://www.akc.org/dog-breeds/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)

    def get_breed_links(self):
        response = requests.get(self.base_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        breeds = []

        breed_cards = soup.find_all('div', {'class': 'breed-card'})
        for card in breed_cards:
            link = card.find('a')
            if link:
                breeds.append({
                    'name': link.text.strip(),
                    'url': link['href']
                })
        return breeds

    def get_breed_details(self, url):
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        details = {}
        details['url'] = url
        details['name'] = soup.find('h1', {'class': 'breed-hero__title'}).text.strip(
        ) if soup.find('h1', {'class': 'breed-hero__title'}) else None

        # Get vital stats
        vital_stats = soup.find('div', {'class': 'vital-stat-box'})
        if vital_stats:
            stats = vital_stats.find_all('div', {'class': 'vital-stat-item'})
            for stat in stats:
                key = stat.find(
                    'div', {'class': 'vital-stat-key'}).text.strip().lower().replace(' ', '_')
                value = stat.find(
                    'div', {'class': 'vital-stat-value'}).text.strip()
                details[key] = value

        return details

    def scrape_all_breeds(self):
        breeds = self.get_breed_links()
        all_breeds_data = []

        print(f"Found {len(breeds)} breeds to process")

        for i, breed in enumerate(breeds, 1):
            print(f"Processing {breed['name']} ({i}/{len(breeds)})")
            try:
                details = self.get_breed_details(breed['url'])
                if details:
                    all_breeds_data.append(details)
                time.sleep(2)  # Be nice to the server
            except Exception as e:
                print(f"Error processing {breed['name']}: {str(e)}")

        return all_breeds_data

    def save_data(self, data):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save as CSV
        csv_path = os.path.join(self.output_dir, f'dog_breeds_{timestamp}.csv')
        pd.DataFrame(data).to_csv(csv_path, index=False)
        print(f"Data saved to {csv_path}")

        # Save as JSON
        json_path = os.path.join(
            self.output_dir, f'dog_breeds_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to {json_path}")


def main():
    scraper = AKCScraper()
    print("Starting AKC breed data collection...")
    data = scraper.scrape_all_breeds()
    scraper.save_data(data)
    print("Data collection complete!")


if __name__ == "__main__":
    main()
