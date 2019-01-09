import json
import os

import pandas as pd
import pyrebase
from bs4 import BeautifulSoup
from selenium import webdriver
from tabulate import tabulate

# url = 'http://tatua3.co.ke/'
url = 'https://supa5.co.ke/en/results'
PAGE_LIMIT = 3


def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.notifications": 2
        }
    )
    main_driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', options=chrome_options)
    main_driver.maximize_window()
    return main_driver


driver = get_driver()


def get_data():
    driver.get(url)

    datalist = []
    for page_no in range(1, PAGE_LIMIT):
        driver.get('https://supa5.co.ke/en/results?page=%s' % str(page_no))
        buttons = driver.find_elements_by_link_text('View All Winners')

        for x in range(len(buttons)):
            # WebDriverWait(driver, 10).until(
            #      ec.element_to_be_clickable((By.LINK_TEXT, b.text)))
            buttons = driver.find_elements_by_link_text('View All Winners')
            buttons[x].click()
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table')

            df = pd.read_html(str(table), header=0)
            datalist.append(df[0])

            driver.back()
    return datalist


def store_data():
    datalist = get_data()
    result = pd.concat([pd.DataFrame(datalist[i]) for i in range(len(datalist))], ignore_index=True)

    json_records = result.to_dict('records')
    print(tabulate(result, headers=["Name", "Phone #", "Ticket #", "Purchase Date", "Picks", "Wager", "Winnings"],
                   tablefmt='psql'))

    if os.path.exists('winners.json'):
        os.remove('winners.json')
    with open('winners.json', 'w') as outfile:
        json.dump(json_records, outfile)


#
def load_data(file_name):
    with open(file_name + '.json') as f:
        collected_data = json.load(f)
    return collected_data


def remove_invalid_characters(data_dict):
    data_dict["Phone Number"] = data_dict.pop("Phone #").replace('*', '')
    data_dict['Ticket Number'] = data_dict.pop("Ticket #")
    return data_dict


def load_pyre():
    config = {
        'apiKey': os.getenv('apiKey'),
        'authDomain': os.getenv('authDomain'),
        'databaseURL': os.getenv('databaseURL'),
        'storageBucket': os.getenv('storageBucket')
    }
    pyre = pyrebase.initialize_app(config)
    db = pyre.database()
    # data = {"name": "Mortimer 'Morty' Smith"}
    # db.child('user').child('Morty').set(data)
    return db


def save_data():
    # fb = firebase.FirebaseApplication('https://supa5scraper.firebaseio.com', None)
    db = load_pyre()
    data = load_data('winners')
    for info in data:
        info = remove_invalid_characters(info)
        print(info)
        try:
            db.child('winners').child(info['Name']).set(info)
        except Exception as e:
            print(e)


try:
    store_data()
    save_data()
except Exception as e:
    print(e)
finally:
    driver.close()
