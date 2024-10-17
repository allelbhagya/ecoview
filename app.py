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
        
        title = soup.find('title').get_text() if soup.find('title') else 'No Title'
        paragraphs = soup.find_all('p')
        article_text = "\n".join([p.get_text() for p in paragraphs])
        
        with open(os.path.join(TEXT_DIR, file_name), 'w', encoding='utf-8') as f:
            f.write(f"{title}\n---\n{article_text}")
    except requests.RequestException as e:
        print(f"Failed to scrape {url}: {e}")
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")

@app.route('/')
def index():
    articles = []
    
    with open('websites.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL']
            file_name = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            
            if not os.path.exists(os.path.join(TEXT_DIR, file_name)):
                scrape_and_save_text(url, file_name)
            
            with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
                title = f.readline().strip() 
            
            articles.append({'title': title, 'file_name': file_name})
    
    return render_template('index.html', articles=articles)

@app.route('/article/<file_name>')
def article(file_name):
    try:
        with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
            title = f.readline().strip()
            f.readline() 
            content = f.read()
        
        return render_template('article.html', title=title, content=content)
    except FileNotFoundError:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
