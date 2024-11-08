from flask import Flask, render_template, abort
import os
import csv
import requests
from bs4 import BeautifulSoup
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk import ngrams
import re

app = Flask(__name__)

TEXT_DIR = 'text'
os.makedirs(TEXT_DIR, exist_ok=True)

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

custom_stop_words = {"would", "use", "should", "could","also"}
stop_words.update(custom_stop_words)

@app.route('/search/<word>')
def search_word(word):
    word = word.lower()
    matching_articles = []
    word_regex = re.escape(word)
    word_regex = re.sub(r"\\s+", r"\\s+", word_regex)
    word_regex = word_regex.replace(r"'", r"'?")
    regex_pattern = re.compile(r'\b' + word_regex + r'\b', re.IGNORECASE)

    for filename in os.listdir(TEXT_DIR):
        with open(os.path.join(TEXT_DIR, filename), 'r', encoding='utf-8') as f:
            title = f.readline().strip()
            f.readline()
            content = f.read().lower()

            if regex_pattern.search(content):
                matching_articles.append({
                    'title': title,
                    'file_name': filename
                })

    return render_template('search_result.html', word=word, articles=matching_articles)

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
    
    top_words_phrases = get_top_words_and_phrases()
    
    return render_template('index.html', articles=articles, top_words_phrases=top_words_phrases)

@app.route('/articles')
def articles():
    articles_list = []
    with open('websites.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL']
            file_name = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            
            if not os.path.exists(os.path.join(TEXT_DIR, file_name)):
                scrape_and_save_text(url, file_name)
            
            with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
                title = f.readline().strip() 
            
            articles_list.append({'title': title, 'file_name': file_name})
    
    return render_template('articles.html', articles=articles_list)

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

def load_and_process_text():
    combined_text = ""
    for filename in os.listdir(TEXT_DIR):
        with open(os.path.join(TEXT_DIR, filename), 'r', encoding='utf-8') as f:
            f.readline()
            f.readline()
            combined_text += f.read() + " "
    return combined_text

def get_top_words_and_phrases(n=30):
    text = load_and_process_text()
    text = re.sub(r'[^A-Za-z\s]', '', text)
    
    words = [word.lower() for word in text.split() if word.lower() not in stop_words and len(word) > 1]

    word_counts = Counter(words)
    bigram_counts = Counter(ngrams(words, 2))
    
    top_single_words = word_counts.most_common(n)
    top_bigrams = bigram_counts.most_common(n)
    
    top_words_phrases = []
    
    for word, _ in top_single_words:
        if has_matching_articles(word):
            top_words_phrases.append((word, word_counts[word]))
    
    for bigram, _ in top_bigrams:
        bigram_str = ' '.join(bigram)
        if has_matching_articles(bigram_str):
            top_words_phrases.append((bigram_str, bigram_counts[bigram]))
    
    top_words_phrases = sorted(top_words_phrases, key=lambda x: x[1], reverse=True)[:n]
    
    return top_words_phrases

def has_matching_articles(word):
    word = word.lower()
    word_regex = re.escape(word)
    word_regex = re.sub(r"\\s+", r"\\s+", word_regex)
    word_regex = word_regex.replace(r"'", r"'?")
    regex_pattern = re.compile(r'\b' + word_regex + r'\b', re.IGNORECASE)

    for filename in os.listdir(TEXT_DIR):
        with open(os.path.join(TEXT_DIR, filename), 'r', encoding='utf-8') as f:
            f.readline()  
            f.readline()  
            content = f.read().lower()
            if regex_pattern.search(content):
                return True
    return False

if __name__ == '__main__':
    app.run(debug=True)
