from flask import Flask, render_template, abort, request
import os
import csv
import re
from collections import Counter
from nltk.corpus import stopwords
from nltk import ngrams
import nltk

app = Flask(__name__)

TEXT_DIR = 'delhi'
os.makedirs(TEXT_DIR, exist_ok=True)

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

custom_stop_words = {"would", "use", "should", "could", "also", "news", "said", "live", "latest", "us", "around", "get", "people", "track", "new", "updates", "news live", "follow", "track latest", "latest news", "watch", "advertisement", "years", "plan", "songs", "report", "promotedlisten", "states", "year", "one", "two", "even", "since", "per"}
stop_words.update(custom_stop_words)

@app.route('/')
def index():
    articles = []
    
    with open('web.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL']
            file_name = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            
            try:
                with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
                    title = f.readline().strip()
                articles.append({'file_name': file_name, 'title': title.replace("Title: ", "")})
            except FileNotFoundError:
                print(f"File not found: {file_name}. Skipping this article.")
            except Exception as e:
                print(f"Error reading {file_name}: {e}. Skipping this article.")
    
    top_words_phrases = get_top_words_and_phrases()
    
    return render_template('index.html', articles=articles, top_words_phrases=top_words_phrases)

@app.route('/time')
def articles_by_year():
    year_filter = request.args.get('year', '').strip()
    articles_by_year = []
    top_words_phrases = []

    if year_filter.isdigit():
        for filename in os.listdir(TEXT_DIR):
            with open(os.path.join(TEXT_DIR, filename), 'r', encoding='utf-8') as f:
                title = f.readline().strip()
                date = f.readline().strip()
                
                if year_filter in date:
                    content = f.read().lower()
                    articles_by_year.append(content)

        if articles_by_year:
            combined_text = ' '.join(articles_by_year)
            top_words_phrases = get_top_words_and_phrases_from_text(combined_text)

            if top_words_phrases:
                max_frequency = max(frequency for _, frequency in top_words_phrases)
                max_font_size =75
                top_words_phrases = [
                    (word, int((frequency / max_frequency) * max_font_size))
                    for word, frequency in top_words_phrases
                ]
    
    return render_template('time.html', year_filter=year_filter, articles_by_year=articles_by_year, top_words_phrases=top_words_phrases)


def get_top_words_and_phrases_from_text(text, n=30):
    text = re.sub(r'[^A-Za-z\s]', '', text)
    words = [word.lower() for word in text.split() if word.lower() not in stop_words and len(word) > 1]
    word_counts = Counter(words)
    bigram_counts = Counter(ngrams(words, 2))

    top_single_words = word_counts.most_common(n)
    top_bigrams = bigram_counts.most_common(n)

    top_words_phrases = [(word, freq) for word, freq in top_single_words] + [(' '.join(bigram), freq) for bigram, freq in top_bigrams]
    return sorted(top_words_phrases, key=lambda x: x[1], reverse=True)[:n]


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
                    'title': title.replace("Title: ", ""),
                    'file_name': filename
                })

    return render_template('search_result.html', word=word, articles=matching_articles)

@app.route('/articles')
def articles():
    articles_list = []
    with open('web.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL']
            file_name = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            
            try:
                with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
                    title = f.readline().strip()
                
                articles_list.append({'file_name': file_name, 'title': title.replace("Title: ", "")})
            except FileNotFoundError:
                print(f"File not found: {file_name}. Skipping this article.")
            except Exception as e:
                print(f"Error reading {file_name}: {e}. Skipping this article.")
    
    return render_template('articles.html', articles=articles_list)

import math
import re


def compute_tf(text):
    words = re.sub(r'[^A-Za-z\s]', '', text).lower().split()
    word_count = Counter(words)
    total_words = len(words)
    tf_scores = {word: count / total_words for word, count in word_count.items()}
    return tf_scores

def compute_idf(all_texts):
    num_documents = len(all_texts)
    word_document_count = Counter()

    for text in all_texts:
        words = set(re.sub(r'[^A-Za-z\s]', '', text).lower().split())
        for word in words:
            word_document_count[word] += 1
    
    idf_scores = {}
    for word, doc_count in word_document_count.items():
        idf_scores[word] = math.log(num_documents / (1 + doc_count)) + 1
    return idf_scores

def compute_tfidf(text, idf_scores):
    tf_scores = compute_tf(text)
    tfidf_scores = {word: tf * idf_scores.get(word, 0) for word, tf in tf_scores.items()}
    return tfidf_scores

def get_top_sentences(text, n=3):
    sentences = re.split(r'(?<=[.!?]) +', text.strip()) 
    all_texts = [sentence for sentence in sentences] 
    idf_scores = compute_idf(all_texts)

    sentence_scores = []
    for sentence in sentences:
        tfidf_scores = compute_tfidf(sentence, idf_scores)
        sentence_score = sum(tfidf_scores.values())
        sentence_scores.append((sentence, sentence_score))

    sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    top_sentences = [sentence for sentence, _ in sorted_sentences[:n]]
    
    return ' '.join(top_sentences)


@app.route('/article/<file_name>')
def article(file_name):
    try:
        with open(os.path.join(TEXT_DIR, file_name), 'r', encoding='utf-8') as f:
            title = f.readline().strip() 
            date = f.readline().strip()
            content = f.read()
        
        summary = get_top_sentences(content, n=6)
        
        return render_template('article.html', title=title.replace("Title: ", ""), date=date, content=content, summary=summary)
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
