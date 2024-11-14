import os
import csv
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

SAVE_DIR = 'delhi'
os.makedirs(SAVE_DIR, exist_ok=True)

def scrape_and_save_text(url, file_name):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title').get_text() if soup.find('title') else 'No Title'
        date_text = 'Unknown Date'
        
        date_element = soup.find(text=re.compile(r'Updated:?\s*[A-Za-z]+\s\d{1,2},\s\d{4}'))
        if date_element:
            date_text = date_element.strip()
            try:
                datetime_obj = datetime.strptime(date_text, ': %B %d, %Y')
                date_text = datetime_obj.strftime('%B %d, %Y')
            except ValueError:
                pass

        paragraphs = soup.find_all('p')
        article_text = "\n".join([p.get_text() for p in paragraphs])
        
        scraped_date = datetime.now().strftime('%B %d, %Y %H:%M:%S')
        
        article_text = re.sub(r"Track Latest News.*", "", article_text, flags=re.DOTALL)
        
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"{date_text}\n")
            f.write("Content:\n")
            f.write(article_text)
        
        print(f"File saved successfully: {file_path}")
    except requests.RequestException as e:
        print(f"Failed to scrape {url}: {e}")
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")

def scrape_articles_from_csv(csv_file_path):
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL']
            file_name = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            if not os.path.exists(os.path.join(SAVE_DIR, file_name)):
                scrape_and_save_text(url, file_name)

csv_file_path = 'web.csv'
scrape_articles_from_csv(csv_file_path)
