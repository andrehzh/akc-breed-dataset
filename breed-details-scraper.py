import requests
from bs4 import BeautifulSoup
import json
import re
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os
from tqdm import tqdm
import time


class BreedDetailsScraper:
    def __init__(self):
        self.base_url = "https://www.akc.org/dog-breeds/"
        # Load database configuration
        load_dotenv()
        self.db_params = {
            'dbname': os.getenv('DB_NAME', 'dog_breeds_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.conn = psycopg2.connect(**self.db_params)
        self.cur = self.conn.cursor()

    def get_breed_data(self, breed_name):
        """Scrapes breed details from AKC website"""
        url = f"{self.base_url}{breed_name}/"

        try:
            # Make request to get the page
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the data-js-props attribute that contains all the breed info
            breed_div = soup.find('div', {'data-js-component': 'breedPage'})
            if not breed_div:
                return self._get_empty_breed_data(breed_name)

            # Parse the JSON data from the data-js-props attribute
            breed_json = json.loads(breed_div['data-js-props'])
            breed_data = breed_json['settings']['breed_data']

            # Safely get nested values with defaults
            basics = breed_data.get('basics', {}).get(breed_name, {})
            traits = breed_data.get('traits', {}).get(breed_name, {})
            trait_scores = traits.get('traits', {})
            health = breed_data.get('health', {}).get(breed_name, {})

            # Helper function to get trait score with validation
            def get_trait_score(trait_name):
                try:
                    score = trait_scores.get(trait_name, {}).get('score')
                    # Ensure score is between 1-5, otherwise return None
                    return score if score and 1 <= int(score) <= 5 else None
                except (TypeError, ValueError):
                    return None

            # Extract basic information with defaults for missing data
            breed_info = {
                "name": basics.get('breed_name', breed_name),
                "breed_group": basics.get('breed_group'),
                "origin": basics.get('origin'),
                "temperament": traits.get('temperament'),
                "life_expectancy": basics.get('life_expectancy'),
                "year_recognized": basics.get('year_recognized'),
                "popularity": basics.get('popularity_2023'),
                "grooming": self._clean_html(health.get('akc_org_grooming', '')),
                "exercise": self._clean_html(health.get('akc_org_exercise', '')),
                "nutrition": self._clean_html(health.get('akc_org_nutrition', '')),
                "health": self._clean_html(health.get('akc_org_health', '')),
                "training": self._clean_html(health.get('akc_org_training', '')),
                "traits": {
                    "adaptability": get_trait_score('adaptability_level'),
                    "affectionate_with_family": get_trait_score('affectionate_with_family'),
                    "barking_level": get_trait_score('barking_level'),
                    "coat_grooming_frequency": get_trait_score('coat_grooming_frequency'),
                    "drooling_level": get_trait_score('drooling_level'),
                    "energy_level": get_trait_score('energy_level'),
                    "good_with_other_dogs": get_trait_score('good_with_other_dogs'),
                    "good_with_young_children": get_trait_score('good_with_young_children'),
                    "mental_stimulation_needs": get_trait_score('mental_stimulation_needs'),
                    "openness_to_strangers": get_trait_score('openness_to_strangers'),
                    "playfulness_level": get_trait_score('playfulness_level'),
                    "shedding_level": get_trait_score('shedding_level'),
                    "trainability_level": get_trait_score('trainability_level'),
                    "watchdog_protective_nature": get_trait_score('watchdogprotective_nature')
                }
            }

            # Handle coat type and length with better defaults
            coat_type = trait_scores.get('coat_type', {}).get('selected')
            coat_length = trait_scores.get('coat_length', {}).get('selected')

            breed_info["coat_type"] = coat_type if coat_type else None
            breed_info["coat_length"] = coat_length if coat_length else None

            return breed_info

        except Exception as e:
            print(f"Error scraping {breed_name}: {e}")
            return self._get_empty_breed_data(breed_name)

    def _get_empty_breed_data(self, breed_name):
        """Returns an empty breed data structure with the breed name"""
        return {
            "name": breed_name,
            "breed_group": None,
            "origin": None,
            "temperament": None,
            "life_expectancy": None,
            "year_recognized": None,
            "popularity": None,
            "grooming": None,
            "exercise": None,
            "nutrition": None,
            "health": None,
            "training": None,
            "traits": {
                "adaptability": None,
                "affectionate_with_family": None,
                "barking_level": None,
                "coat_grooming_frequency": None,
                "drooling_level": None,
                "energy_level": None,
                "good_with_other_dogs": None,
                "good_with_young_children": None,
                "mental_stimulation_needs": None,
                "openness_to_strangers": None,
                "playfulness_level": None,
                "shedding_level": None,
                "trainability_level": None,
                "watchdog_protective_nature": None
            },
            "coat_type": None,
            "coat_length": None
        }

    def _clean_html(self, html_content):
        """Removes HTML tags from content"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text().strip()

    def insert_breed_data(self, breed_data):
        """Insert breed data into database"""
        try:
            query = """
                INSERT INTO dog_breeds (
                    name, breed_group, origin, temperament, life_expectancy,
                    year_recognized, popularity, grooming, exercise, nutrition,
                    health, training, adaptability, affectionate_with_family,
                    barking_level, coat_grooming_frequency, drooling_level,
                    energy_level, good_with_other_dogs, good_with_young_children,
                    mental_stimulation_needs, openness_to_strangers,
                    playfulness_level, shedding_level, trainability_level,
                    watchdog_protective_nature, coat_type, coat_length
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            # Prepare coat arrays, ensuring they're never empty
            coat_type = [breed_data['coat_type']
                         ] if breed_data['coat_type'] else ['Unknown']
            coat_length = [breed_data['coat_length']
                           ] if breed_data['coat_length'] else ['Unknown']

            values = (
                breed_data['name'],
                breed_data['breed_group'],
                breed_data['origin'],
                breed_data['temperament'],
                breed_data['life_expectancy'],
                breed_data['year_recognized'],
                breed_data['popularity'],
                breed_data['grooming'] or None,  # Convert empty string to None
                breed_data['exercise'] or None,
                breed_data['nutrition'] or None,
                breed_data['health'] or None,
                breed_data['training'] or None,
                breed_data['traits']['adaptability'],
                breed_data['traits']['affectionate_with_family'],
                breed_data['traits']['barking_level'],
                breed_data['traits']['coat_grooming_frequency'],
                breed_data['traits']['drooling_level'],
                breed_data['traits']['energy_level'],
                breed_data['traits']['good_with_other_dogs'],
                breed_data['traits']['good_with_young_children'],
                breed_data['traits']['mental_stimulation_needs'],
                breed_data['traits']['openness_to_strangers'],
                breed_data['traits']['playfulness_level'],
                breed_data['traits']['shedding_level'],
                breed_data['traits']['trainability_level'],
                breed_data['traits']['watchdog_protective_nature'],
                coat_type,
                coat_length
            )

            self.cur.execute(query, values)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting {breed_data['name']}: {e}")
            return False

    def process_all_breeds(self, json_file):
        """Process all breeds from JSON file"""
        try:
            with open(json_file, 'r') as f:
                breeds = json.load(f)

            print(f"Found {len(breeds)} breeds to process")

            for breed in tqdm(breeds, desc="Processing breeds"):
                # Extract breed name from URL
                breed_name = breed['url'].split('/')[-2]

                # Check if breed already exists in database
                self.cur.execute(
                    "SELECT name FROM dog_breeds WHERE name = %s", (breed['name'],))
                if self.cur.fetchone():
                    print(
                        f"Skipping {breed['name']} - already exists in database")
                    continue

                # Get breed data
                breed_data = self.get_breed_data(breed_name)

                if breed_data:
                    if self.insert_breed_data(breed_data):
                        print(f"Successfully processed {breed['name']}")
                    else:
                        print(f"Failed to insert {breed['name']}")
                else:
                    print(f"Failed to get data for {breed['name']}")

                # Be nice to the server
                time.sleep(2)

        except Exception as e:
            print(f"Error processing breeds: {e}")
        finally:
            self.cur.close()
            self.conn.close()


def main():
    scraper = BreedDetailsScraper()

    # Use the most recent JSON file in the output directory
    json_files = [f for f in os.listdir('output') if f.endswith('.json')]
    if not json_files:
        print("No JSON files found in output directory")
        return

    latest_json = max([os.path.join('output', f)
                      for f in json_files], key=os.path.getctime)
    print(f"Using {latest_json}")

    scraper.process_all_breeds(latest_json)


if __name__ == "__main__":
    main()
