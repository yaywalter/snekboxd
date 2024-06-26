# Standard library imports
import importlib
import subprocess
import sys
import csv
import random
import os
import shutil
import hashlib
import re
import logging
import tkinter as tk
from collections import deque
from tkinter import messagebox

# Install and import 3rd-party libraries
def install(package_name,import_name=None):
    if import_name == None:
        import_name = package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"{package_name} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

install('Pillow','PIL')
install('requests')
install('beautifulsoup4','bs4')

from PIL import Image, ImageTk
from bs4 import BeautifulSoup
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def get_file_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

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

class MovieRankingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Movie Ranking App")
        self.master.geometry("1920x1080")

        self.original_file = './db/ratings.csv'
        self.working_file = './db/working_ratings.csv'
        self.diff_file = './db/changed_ratings.csv'

        self.no_image_md5 = get_file_md5('./assets/no_image.jpg')

        create_working_copy(self.original_file, self.working_file)
        self.movies = load_csv(self.working_file)
        self.bag = create_movie_bag(self.movies)

        self.bag_cycle_count = 1
        self.total_ranked_count = 0
        self.movies_in_bag = len(self.bag)

        self.selected_movies = []
        self.movie_frames = []

        # Create a main frame to hold all elements
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Create a frame for the movies
        self.movies_frame = tk.Frame(self.main_frame)
        self.movies_frame.pack(expand=True, fill=tk.BOTH, pady=20)

        # Create a frame for the input and buttons
        self.input_frame = tk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=20)

        # Create a frame for the counters
        self.counter_frame = tk.Frame(self.main_frame)
        self.counter_frame.pack(fill=tk.X, pady=20)

        self.bag_cycle_label = tk.Label(self.counter_frame, text="Bag Cycles: 1", font=('Arial', 14))
        self.bag_cycle_label.pack(side=tk.LEFT, padx=(0, 20))

        self.total_ranked_label = tk.Label(self.counter_frame, text="Total Ranked: 0", font=('Arial', 14))
        self.total_ranked_label.pack(side=tk.LEFT, padx=(0, 20))

        self.movies_in_bag_label = tk.Label(self.counter_frame, text=f"Movies in Bag: {self.movies_in_bag}", font=('Arial', 14))
        self.movies_in_bag_label.pack(side=tk.LEFT)

        self.ranking_entry = tk.Entry(self.input_frame, font=('Arial', 24), width=10)
        self.ranking_entry.pack(side=tk.LEFT, padx=(0, 20))

        self.submit_button = tk.Button(self.input_frame, text="Submit Ranking", command=self.submit_ranking, font=('Arial', 18))
        self.submit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.quit_button = tk.Button(self.input_frame, text="Quit", command=self.quit_app, font=('Arial', 18))
        self.quit_button.pack(side=tk.LEFT)

        self.master.bind('<Return>', lambda event: self.submit_ranking())
        self.master.bind('<Tab>', lambda event: self.submit_ranking())
        self.master.bind('<Escape>', lambda event: self.quit_app())

        self.submit_button.config(takefocus=0)
        self.quit_button.config(takefocus=0)

        self.master.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.load_new_movies()

    def fetch_missing_posters(self):
        for movie in self.selected_movies:
            if os.path.exists(movie.image_path):
                if get_file_md5(movie.image_path) == self.no_image_md5:
                    logging.info(f"Fetching poster for {movie.name}")
                    poster_url = get_tmdb_poster_url(movie.uri)
                    if poster_url:
                        if download_poster(poster_url, movie.image_path):
                            logging.info(f"Successfully downloaded poster for {movie.name}")
                        else:
                            logging.error(f"Failed to download poster for {movie.name}")
                    else:
                        logging.error(f"Poster not found for {movie.name}")

    def load_new_movies(self):
        for frame in self.movie_frames:
            frame.destroy()
        self.movie_frames.clear()

        # If fewer than two movies are left, refill the bag
        if len(self.bag) < 2:
            if len(self.bag) > 0:
                self.bag.popleft() # If remainder of 1, remove to prevent duplicates appearing together in a round.
            self.bag.extend(self.movies)
            shuffle_deque(self.bag)
            self.bag_cycle_count += 1
            self.bag_cycle_label.config(text=f"Bag Cycles: {self.bag_cycle_count}")

        # Select up to 5 movies
        num_movies = min(5, len(self.bag))
        self.selected_movies = select_movies(self.bag, num_movies)
        self.fetch_missing_posters()

        # Update movies in bag counter
        self.movies_in_bag = len(self.bag)
        self.movies_in_bag_label.config(text=f"Movies in Bag: {self.movies_in_bag}")
        
        # Sort selected movies by their current rating, lowest to highest
        self.selected_movies.sort(key=lambda movie: movie.rating)

        # Calculate dynamic padding and image size based on number of movies
        padx = max(10, int(100 / num_movies))
        img_width = min(450, int(1400 / num_movies))
        img_height = int(img_width * 1.5)  # Maintain aspect ratio

        for i, movie in enumerate(self.selected_movies, 1):
            frame = tk.Frame(self.movies_frame)
            frame.pack(side=tk.LEFT, padx=padx, expand=True)

            if movie.image_path:
                img = Image.open(movie.image_path)
                img = img.resize((img_width, img_height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(frame, image=photo)
                label.image = photo
                label.pack()

            # Adjust font sizes based on number of movies
            title_font_size = max(12, int(20 - num_movies))
            rating_font_size = max(10, int(18 - num_movies))

            tk.Label(frame, text=f"{i}. {movie.name}\n({movie.year})", wraplength=img_width, font=('Arial', title_font_size)).pack()
            tk.Label(frame, text=f"Rating: {movie.rating}", font=('Arial', rating_font_size)).pack()

            self.movie_frames.append(frame)

        self.ranking_entry.delete(0, tk.END)
        self.ranking_entry.focus_set()

    def submit_ranking(self):
        ranking = self.ranking_entry.get()
        num_movies = len(self.selected_movies)
        if len(ranking) == num_movies and ranking.isdigit() and set(ranking) == set(map(str, range(1, num_movies + 1))):
            ranking = [int(r) - 1 for r in ranking]
            update_ratings(self.selected_movies, ranking)
            save_csv(self.working_file, self.movies)
            self.total_ranked_count += num_movies
            self.total_ranked_label.config(text=f"Total Ranked: {self.total_ranked_count}")
            self.load_new_movies()
        else:
            self.ranking_entry.delete(0, tk.END)
        
        self.ranking_entry.focus_set()

    def quit_app(self):
        compare_csvs(self.original_file, self.working_file, self.diff_file)
        print(f"Changes saved to {self.diff_file}")

        create_working_copy(self.working_file, self.original_file)

        try:
            os.remove(self.working_file)
            print(f"Successfully deleted {self.working_file}")
        except OSError as e:
            print(f"Error deleting {self.working_file}: {e}")

        self.master.quit()
        
def main():
    root = tk.Tk()
    app = MovieRankingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()