import hashlib, random, csv, re, logging, os, importlib, subprocess, sys, shutil
from collections import deque
from datetime import datetime


def install(package_name,import_name=None):
    if import_name == None:
        import_name = package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"{package_name} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

install('requests')
import requests

install('beautifulsoup4','bs4')
from bs4 import BeautifulSoup

class Movie:
    def __init__(self, date, name, year, uri, rating):
        self.date = date
        self.name = name
        self.year = year
        self.uri = uri
        self.rating = float(rating)
        self.image_path = self.get_image_path()

    def get_image_path(self):
        uri_id = self.uri.split('/')[-1]
        image_path = f'./images/{sanitize_filename(self.name)} ({uri_id}).jpg'
        if not os.path.exists(image_path):
            no_image_path = './assets/no_image.jpg'
            if os.path.exists(no_image_path):
                shutil.copy(no_image_path, image_path)
                return image_path
            else:
                return None
        return image_path

def get_file_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

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
            return True
        else:
            logging.error(f"Content is not an image for {filename}. Content-Type: {content_type}")
    else:
        logging.error(f"Failed to download: {filename}. Status code: {response.status_code}")
    return False

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

def shuffle_deque(d):
    l = list(d)
    random.shuffle(l)
    d.clear()
    d.extend(l)

def sanitize_filename(filename):
    # Remove or replace characters that are invalid in filenames
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def validated_rating_input(message):
    valid = False
    rating = 0

    while not valid:
        print(message)
        rating = input()
        try:
            rating = float(rating)
            valid = True
        except:
            print("Rating must be a number.\n")
            valid = False

        if valid:
            rating = round(rating * 2) / 2 # Round to nearest 0.5
            if 0.5 <= rating <= 5.0:
                return str(rating)
            else:
                print("Rating must be between 0.5 and 5.\n")
                valid = False

def validated_year_input(message):
    valid = False
    current_year = datetime.now().year
    year = 0

    while not valid:
        print(message)
        year = input()
        try:
            year = int(year)
            valid = True
        except:
            print("Year must be an integer.\n")
            valid = False
        
        if valid:
            if 1874 <= year <= (current_year+1):
                return year
            else:
                print(f"Year must be between 1874 and {current_year+1}.\n")
                valid = False
           

def validated_uri_input(message):
    pattern = r'^https://boxd\.it/[a-zA-Z0-9]{1,4}$'

    while True:
        print(message)
        uri = input()

        if bool(re.match(pattern,uri)):
            return uri
        else:
            print("Invalid URI.\n")


def load_csv(filename):
    movies = []
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            movies.append(Movie(*row))
    return movies

def save_csv(filename, movies):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])
        for movie in movies:
            writer.writerow([movie.date, movie.name, movie.year, movie.uri, movie.rating])

def create_working_copy(original_file, working_file):
    with open(original_file, 'r', encoding='utf-8') as original:
        with open(working_file, 'w', encoding='utf-8') as working:
            working.write(original.read())

def create_movie_bag(movies):
    return deque(random.sample(movies, len(movies)))

def select_movies(bag, num_movies):
    # Select up to num_movies, but not more than what's in the bag
    num_to_select = min(num_movies, len(bag))
    
    selected = []
    used_ratings = set()
    temp_bag = []
    
    # First pass: select movies with unique ratings
    while bag and len(selected) < num_to_select:
        movie = bag.popleft()
        if movie.rating not in used_ratings:
            selected.append(movie)
            used_ratings.add(movie.rating)
        else:
            temp_bag.append(movie)
    
    # Return unselected movies to the bag
    bag.extend(temp_bag)
    
    # Second pass: fill remaining slots with any movies
    while len(selected) < num_to_select and bag:
        selected.append(bag.popleft())
    
    return selected

def update_ratings(movies, ranking):
    # Sort the movies by their current ratings (highest to lowest)
    sorted_movies = sorted(movies, key=lambda m: m.rating, reverse=True)
    
    # Create a mapping of new positions to current ratings
    new_ratings = {i: movie.rating for i, movie in enumerate(sorted_movies)}
    
    # Assign new ratings based on the user's ranking
    for new_pos, old_pos in enumerate(ranking):
        movies[old_pos].rating = new_ratings[new_pos]

def compare_csvs(original_file, working_file, diff_file):
    original_movies = {(m.name, m.year): m for m in load_csv(original_file)}
    working_movies = {(m.name, m.year): m for m in load_csv(working_file)}
    
    changed_movies = [
        working_movies[(name, year)]
        for (name, year) in original_movies
        if original_movies[(name, year)].rating != working_movies[(name, year)].rating
    ]
    
    save_csv(diff_file, changed_movies)