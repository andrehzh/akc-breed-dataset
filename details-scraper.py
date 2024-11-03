from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time


class DetailsScraper:
    def __init__(self):
        # Setup Chrome options similar to the working breed scraper
        self.chrome_options = Options()
        # self.chrome_options.add_argument('--headless')  # Comment out for debugging
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        # Setup Chrome service
        self.service = Service(ChromeDriverManager().install())

    def get_breed_details(self, url="https://www.akc.org/dog-breeds/affenpinscher/"):
        driver = webdriver.Chrome(
            service=self.service, options=self.chrome_options)
        wait = WebDriverWait(driver, 20)

        try:
            print(f"Accessing URL: {url}")
            driver.get(url)
            time.sleep(5)  # Increased initial wait time

            # Debug: Print page title
            print(f"Page title: {driver.title}")

            breed_data = {
                "breed_name": None,
                "description": None,
                "characteristics": {},
                "vital_stats": {}
            }

            try:
                # Get breed name (this works already)
                breed_name = wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
                breed_data["breed_name"] = breed_name.text.strip()
                print(f"Found breed name: {breed_data['breed_name']}")

                # Get description - updated selector
                try:
                    description = wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div.breed-hero__footer"))
                    )
                    breed_data["description"] = description.text.strip()
                    print(f"Found description: {description.text[:50]}...")
                except Exception as e:
                    print(f"Error getting description: {e}")
                    # Try alternative selector
                    try:
                        description = driver.find_element(
                            By.CSS_SELECTOR, "div.breed-description")
                        breed_data["description"] = description.text.strip()
                        print(
                            f"Found description (alternative): {description.text[:50]}...")
                    except:
                        pass

                # Get characteristics - updated selector
                try:
                    characteristics = driver.find_elements(
                        By.CSS_SELECTOR, "div.breed-characteristics-ratings-item"
                    )
                    for char in characteristics:
                        try:
                            name = char.find_element(
                                By.CSS_SELECTOR, ".breed-characteristics-ratings-name"
                            ).text.strip()
                            stars = len(char.find_elements(
                                By.CSS_SELECTOR, ".icon-full-star"
                            ))
                            breed_data["characteristics"][name] = stars
                            print(f"Found characteristic: {name} = {stars}")
                        except Exception as e:
                            print(f"Error processing characteristic: {e}")
                except Exception as e:
                    print(f"Error getting characteristics section: {e}")

                # Get vital stats - updated selector
                try:
                    vital_stats = driver.find_elements(
                        By.CSS_SELECTOR, "div.vital-stat"
                    )
                    for stat in vital_stats:
                        try:
                            key = stat.find_element(
                                By.CSS_SELECTOR, ".vital-stat-key"
                            ).text.strip()
                            value = stat.find_element(
                                By.CSS_SELECTOR, ".vital-stat-value"
                            ).text.strip()
                            breed_data["vital_stats"][key] = value
                            print(f"Found vital stat: {key} = {value}")
                        except Exception as e:
                            print(f"Error processing vital stat: {e}")
                except Exception as e:
                    print(f"Error getting vital stats section: {e}")

                # Debug: Save page source if we didn't get all data
                if not breed_data["description"] or not breed_data["characteristics"] or not breed_data["vital_stats"]:
                    with open('page_source.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    print("Page source saved to page_source.html for debugging")

            except Exception as e:
                print(f"Error processing breed data: {e}")

            return breed_data

        except Exception as e:
            print(f"Error in get_breed_details: {e}")
            return None
        finally:
            driver.quit()


def main():
    scraper = DetailsScraper()
    breed_data = scraper.get_breed_details()

    if breed_data:
        print("\nSuccessfully scraped breed data:")
        print(json.dumps(breed_data, indent=4, ensure_ascii=False))

        # Save to file
        with open('breed_details.json', 'w', encoding='utf-8') as f:
            json.dump(breed_data, f, indent=4, ensure_ascii=False)
        print("\nData saved to breed_details.json")
    else:
        print("\nFailed to scrape data")


if __name__ == "__main__":
    main()
