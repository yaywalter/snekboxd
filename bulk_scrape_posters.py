import csv
import requests
from bs4 import BeautifulSoup
import time
import os
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_filename(filename):
    # Remove or replace characters that are invalid in filenames
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def download_poster(url, filename):
    response = requests.get(url, headers=get_headers(), allow_redirects=True)
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if 'image' in content_type:
            with open(filename, 'wb') as file:
                file.write(response.content)
            logging.info(f"Downloaded: {filename}")
        else:
            logging.error(f"Content is not an image for {filename}. Content-Type: {content_type}")
    else:
        logging.error(f"Failed to download: {filename}. Status code: {response.status_code}")

def get_tmdb_poster_url(letterboxd_url):
    response = requests.get(letterboxd_url, headers=get_headers(), allow_redirects=True)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tmdb_link = soup.find('a', {'data-track-action': 'TMDb'})
        if tmdb_link and 'href' in tmdb_link.attrs:
            tmdb_url = tmdb_link['href']
            tmdb_response = requests.get(tmdb_url, headers=get_headers(), allow_redirects=True)
            if tmdb_response.status_code == 200:
                tmdb_soup = BeautifulSoup(tmdb_response.text, 'html.parser')
                og_image = tmdb_soup.find('meta', property='og:image')
                if og_image and 'content' in og_image.attrs:
                    return og_image['content']
    return None

def process_csv(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            letterboxd_url = row['Letterboxd URI']
            movie_id = letterboxd_url.split('/')[-1]
            movie_name = row['Name']
            
            logging.info(f"Processing: {row['Name']} ({letterboxd_url})")
            
            poster_url = get_tmdb_poster_url(letterboxd_url)
            if poster_url:
                filename = f"./images/{sanitize_filename(movie_name)}_{movie_id}.jpg"
                download_poster(poster_url, filename)
            else:
                logging.error(f"Poster not found for {row['Name']}")
            
            # Delay to avoid overwhelming the server
            time.sleep(1)

if __name__ == "__main__":
    csv_file = "./db/original_ratings.csv"
    if os.path.exists(csv_file):
        process_csv(csv_file)
    else:
        logging.error(f"Error: {csv_file} not found in the current directory.")
