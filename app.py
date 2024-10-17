from flask import Flask, render_template, abort
import os
import csv
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

TEXT_DIR = 'text'
os.makedirs(TEXT_DIR, exist_ok=True)

def scrape_and_save_text(url, file_name):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title and text
        title = soup.find('title').get_text() if soup.find('title') else 'No Title'
        paragraphs = soup.find_all('p')
        article_text = "\n".join([p.get_text() for p in paragraphs])
        
        # Save title and article text in the file
        with open(os.path.join(TEXT_DIR, file_name), 'w', encoding='utf-8') as f:
            f.write(f"{title}\n---\n{article_text}")
    except requests.RequestException as e:
        print(f"Failed to scrape {url}: {e}")
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")

@app.route('/')
def index():
    articles = []
    
    # Read from the CSV file to gather URLs and corresponding file names
    with open('websites.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL']
            file_name = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            
            # Ensure the file exists after scraping
            if not os.path.exists(os.path.join(TEXT_DIR, file_name)):
                scrape_and_save_text(url, file_name)
            
            # Extract title from the saved file
            with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
                title = f.readline().strip()  # Read the first line (title)
            
            articles.append({'title': title, 'file_name': file_name})
    
    # Render the list of articles in the index.html template
    return render_template('index.html', articles=articles)

@app.route('/article/<file_name>')
def article(file_name):
    try:
        # Read the file content
        with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
            title = f.readline().strip()  # Read the first line (title)
            f.readline()  # Skip the separator line (---)
            content = f.read()  # Read the rest of the content (article text)
        
        return render_template('article.html', title=title, content=content)
    except FileNotFoundError:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
