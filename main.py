import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging

logging.basicConfig(filename='scraping.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

def get_multiple_pages_data(page_limit):
    all_links = []
    with tqdm(total=page_limit, desc='Processing') as pbar:
        for page_number in range(1, page_limit + 1):
            try:
                url = f'https://news.ycombinator.com/news?p={page_number}'
                res = requests.get(url)
                soup = BeautifulSoup(res.text, 'html.parser')
                links = soup.select('.titleline > a')
                subtext = soup.select('.subtext')

                hn = create_custom_hn(links, subtext)
                all_links.extend(hn)
                pbar.update(1)
            except requests.RequestException as e:
                logging.error(f"An error occurred while processing page {page_number}: {e}")
                raise
            except ValueError as e:
                logging.error(f"Value error occurred while processing page {page_number}: {e}")
                raise

    return all_links


def sort_stories_by_votes(hnlist):
    return sorted(hnlist, key=lambda k: k['votes'], reverse=True)


def create_custom_hn(links, subtext):
    hn = []
    for idx, item in enumerate(links):
        title = item.getText()
        href = item.get('href', None)
        vote = subtext[idx].select(".score")
        if len(vote):
            points = int(vote[0].getText().replace(' points', ''))
            if points > 199:
                hn.append({'title': title, 'link': href, 'votes': points})
    return sort_stories_by_votes(hn)


def get_validated_input(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Please enter a valid integer.")


pages_to_scrape = get_validated_input("Enter the number of pages to scrape: ")

try:
    results = get_multiple_pages_data(pages_to_scrape)
    save_to_excel(sort_stories_by_votes(results), input('Name the file: ') + '.xlsx')
    print("Scraping completed successfully!")
except Exception as e:
    print(f"An error occurred: {e}")
