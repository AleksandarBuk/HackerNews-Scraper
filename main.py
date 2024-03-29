import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging
from datetime import date
import os
import click

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

from datetime import date, datetime, timedelta


def parse_date(date_str):
    if 'day' in date_str:
        days_ago = int(date_str.split()[0])
        post_date = date.today() - timedelta(days=days_ago)
    elif 'hour' in date_str:
        hours_ago = int(date_str.split()[0])
        post_date = datetime.now() - timedelta(hours=hours_ago)
    elif 'minute' in date_str:
        minutes_ago = int(date_str.split()[0])
        post_date = datetime.now() - timedelta(minutes=minutes_ago)
    else:
        post_date = date.today()
    return post_date


def create_custom_hn(links, subtext):
    hn = []
    for idx, item in enumerate(links):
        title = item.getText()
        href = item.get('href', None)
        vote = subtext[idx].select(".score")
        date_str = subtext[idx].select(".age")[0].getText()

        if len(vote):
            points = int(vote[0].getText().replace(' points', ''))
            post_date = parse_date(date_str)
            if points > 199:
                hn.append({'title': title, 'link': href, 'votes': points, 'date': post_date.strftime('%Y-%m-%d')})
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

@click.command()
@click.option('-p', '--pages', default=10, help='Number of pages to scrape')
@click.option('-o', '--output', default=f'f1_{date.today()}.xlsx', help='Name of the output file')
def scrape(pages, output):
    """Scrape data from Hacker News
        excel:Title, Link, Votes, Date
    """
    try:
        output_dir = '../ScrapedData'
        result = get_multiple_pages_data(pages)
        filename = output
        excel_filename = os.path.join(output_dir, filename)
        sorted_result = sort_stories_by_votes(result)

        save_to_excel(sorted_result, excel_filename)

        print("Scraping completed successfuly")
        print("File saved", excel_filename)

        excel_data = pd.read_excel(excel_filename)

        print(f'Recently scraped: ')
        print(excel_data)

    except Exception as e:
        print(f'An error occured: {e}')


if __name__ == "__main__":
    scrape()