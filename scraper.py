import json
from bs4 import BeautifulSoup
import re


def extract_breed_data(html_content):
    # Find the data-js-props attribute content
    soup = BeautifulSoup(html_content, 'html.parser')
    breed_div = soup.find('div', {'data-js-component': 'breedPage'})

    if not breed_div:
        return None

    # Parse the JSON data from the data-js-props attribute
    json_data = json.loads(breed_div['data-js-props'])

    # Get breed name from URL
    breed_name = json_data['settings']['current_breed']

    # Extract data from the JSON structure
    breed_data = {
        'name': json_data['settings']['basics'][breed_name]['breed_name'],
        'group': json_data['settings']['basics'][breed_name]['breed_group'],
        'height': None,  # Not directly available in JSON
        'weight': None,  # Not directly available in JSON
        'life_expectancy': json_data['settings']['basics'][breed_name]['life_expectancy'],
        'temperament': json_data['settings']['traits'][breed_name]['temperament'],
        'origin': json_data['settings']['basics'][breed_name]['origin'],
        'description': json_data['settings']['description'][breed_name]['akc_org_about'].strip('<p>').strip('</p>'),
        'grooming': json_data['settings']['health'][breed_name]['akc_org_grooming'].strip('<p>').strip('</p>'),
        'health': json_data['settings']['health'][breed_name]['akc_org_health'].strip('<p>').strip('</p>')
    }

    return breed_data
