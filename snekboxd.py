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
from tkinter import ttk
from collections import deque
from tkinter import messagebox
from datetime import datetime


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

def validate_rating(input_rating):
    try:
        rating = float(input_rating)
    except:
        raise TypeError("Rating must be a number!")
        
    rounded_rating = round(rating * 2) / 2  # Round to nearest 0.5
    if 0.5 <= rounded_rating <= 5.0:
        return rounded_rating
    else:
        raise ValueError(f"Rating {rating} is outside the valid range of 0.5 to 5.0")

def validate_year(input_year):
    current_year = datetime.now().year

    try:
        year = int(input_year)
    except:
        raise TypeError("Year must be an integer")
    
    if 1874 <= year <= (current_year+1):
        return year
    else:
        raise ValueError(f"Year {year} is outside the valid range of 1874 to {current_year+1}")

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
        self.master.title("Snekboxd")
        
        # Get screen width and height
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        
        # Set initial window size to 90% of screen size
        self.window_width = int(self.screen_width * 0.9)
        self.window_height = int(self.screen_height * 0.9)
        
        # Calculate x and y coordinates for the Tk root window
        x = (self.screen_width // 2) - (self.window_width // 2)
        y = (self.screen_height // 2) - (self.window_height // 2)
        
        # Set the dimensions of the screen and where it is placed
        self.master.geometry(f'{self.window_width}x{self.window_height}+{x}+{y}')

        # Make window resizable
        self.master.resizable(True, True)

        # Initialize fullscreen state
        self.fullscreen = False

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
        self.previous_movies = None
        self.movie_frames = []

        # Create a main frame to hold all elements
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Create a frame for the movies
        self.movies_frame = ttk.Frame(self.main_frame)
        self.movies_frame.pack(expand=True, fill=tk.BOTH, pady=20)

        # Create a frame for the input and buttons
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=20)

        # Create a frame for the counters
        self.counter_frame = ttk.Frame(self.main_frame)
        self.counter_frame.pack(fill=tk.X, pady=20)

        self.bag_cycle_label = ttk.Label(self.counter_frame, text="Bag Cycles: 1", font=('Arial', 14))
        self.bag_cycle_label.pack(side=tk.LEFT, padx=(0, 20))

        self.total_ranked_label = ttk.Label(self.counter_frame, text="Total Ranked: 0", font=('Arial', 14))
        self.total_ranked_label.pack(side=tk.LEFT, padx=(0, 20))

        self.movies_in_bag_label = ttk.Label(self.counter_frame, text=f"Movies in Bag: {self.movies_in_bag}", font=('Arial', 14))
        self.movies_in_bag_label.pack(side=tk.LEFT)

        self.ranking_entry = ttk.Entry(self.input_frame, font=('Arial', 24), width=10)
        self.ranking_entry.pack(side=tk.LEFT, padx=(0, 20))

        self.submit_button = ttk.Button(self.input_frame, text="Submit Ranking", command=self.submit_ranking, takefocus=0)
        self.submit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.quit_button = ttk.Button(self.input_frame, text="Quit", command=self.quit_app, takefocus=0)
        self.quit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.undo_button = ttk.Button(self.input_frame, text="Undo", command=self.undo_last, takefocus=0)
        self.undo_button.pack(side=tk.LEFT)

        self.master.bind('<Return>', lambda event: self.submit_ranking())
        self.master.bind('<Tab>', lambda event: self.submit_ranking())
        self.master.bind('<Escape>', lambda event: self.quit_app())

        self.master.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Modify the binding for window resizing
        self.master.bind("<Configure>", self.on_resize)

        # Add binding for fullscreen toggle
        self.master.bind("<Command-f>", self.toggle_fullscreen)

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

    def on_resize(self, event):
        # This method is called whenever the window is resized
        if event.widget == self.master and not self.fullscreen:
            # Update window size variables
            self.window_width = event.width
            self.window_height = event.height
            # Delay the layout update to avoid excessive redraws
            self.master.after_cancel(self.resize_job) if hasattr(self, 'resize_job') else None
            self.resize_job = self.master.after(100, self.update_layout)

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.master.attributes("-fullscreen", self.fullscreen)
        self.update_layout()

    def end_fullscreen(self, event=None):
        self.fullscreen = False
        self.master.attributes("-fullscreen", False)
        self.update_layout()

    def update_layout(self):
        if not self.selected_movies:
            return

        for frame in self.movie_frames:
            frame.destroy()
        self.movie_frames.clear()

        num_movies = len(self.selected_movies)

        # Use current window size for calculations
        if self.fullscreen:
            window_width = self.screen_width
            window_height = self.screen_height
        else:
            window_width = self.window_width
            window_height = self.window_height
        
        # Calculate available width for movies (80% of window width)
        available_width = window_width * 0.8
        
        # Calculate maximum possible image width
        max_img_width = available_width / num_movies
        
        # Set a minimum image width to prevent tiny images
        min_img_width = 50
        
        # Determine the actual image width
        img_width = max(min_img_width, min(200, max_img_width))
        
        # Calculate padding based on available space
        total_image_width = img_width * num_movies
        remaining_width = available_width - total_image_width
        padx = max(2, int(remaining_width / (num_movies + 1)))
        
        # Calculate image height maintaining aspect ratio
        img_height = int(img_width * 1.5)

        # Adjust image height if it's too tall (max 60% of window height)
        max_img_height = int(window_height * 0.6)
        if img_height > max_img_height:
            img_height = max_img_height
            img_width = int(img_height / 1.5)

        for i, movie in enumerate(self.selected_movies, 1):
            frame = ttk.Frame(self.movies_frame)
            frame.pack(side=tk.LEFT, padx=padx, expand=True)

            if movie.image_path:
                img = Image.open(movie.image_path)
                img = img.resize((int(img_width), int(img_height)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack()

            # Adjust font sizes based on image width
            title_font_size = max(8, min(12, int(img_width / 10)))
            rating_font_size = max(6, min(10, int(img_width / 12)))

            ttk.Label(frame, text=f"{i}. {movie.name}\n({movie.year})", wraplength=img_width, font=('Arial', title_font_size)).pack()
            ttk.Label(frame, text=f"Rating: {movie.rating}", font=('Arial', rating_font_size)).pack()

            self.movie_frames.append(frame)

    def load_new_movies(self):
        for frame in self.movie_frames:
            frame.destroy()
        self.movie_frames.clear()

        # If fewer than two movies are left, refill the bag
        if len(self.bag) < 2:
            if len(self.bag) > 0:
                self.bag.popleft()
            self.bag.extend(self.movies)
            shuffle_deque(self.bag)
            self.bag_cycle_count += 1
            self.bag_cycle_label.config(text=f"Bag Cycles: {self.bag_cycle_count}")

        # Select up to 5 movies
        num_movies = min(5, len(self.bag))
        self.selected_movies = select_movies(self.bag, num_movies)

        if mode == "2" and new_movie not in self.selected_movies:
            self.selected_movies.append(new_movie)
        else:
            num_movies -= 1

        self.fetch_missing_posters()

        # Update movies in bag counter
        self.movies_in_bag = len(self.bag)
        self.movies_in_bag_label.config(text=f"Movies in Bag: {self.movies_in_bag}")
        
        # Sort selected movies by their current rating, lowest to highest
        self.selected_movies.sort(key=lambda movie: movie.rating)

        # Calculate dynamic padding and image size based on window size and number of movies
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        
        padx = max(10, int(window_width * 0.02))
        img_width = min(200, int((window_width * 0.8) / num_movies))
        img_height = int(img_width * 1.5)  # Maintain aspect ratio

        # Adjust image size if it's too tall
        if img_height > window_height * 0.6:
            img_height = int(window_height * 0.6)
            img_width = int(img_height / 1.5)

        for i, movie in enumerate(self.selected_movies, 1):
            frame = ttk.Frame(self.movies_frame)
            frame.pack(side=tk.LEFT, padx=padx, expand=True)

            if movie.image_path:
                img = Image.open(movie.image_path)
                img = img.resize((img_width, img_height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack()

            # Adjust font sizes based on window size
            title_font_size = max(10, min(14, int(window_width / 100)))
            rating_font_size = max(8, min(12, int(window_width / 120)))

            ttk.Label(frame, text=f"{i}. {movie.name}\n({movie.year})", wraplength=img_width, font=('Arial', title_font_size)).pack()
            ttk.Label(frame, text=f"Rating: {movie.rating}", font=('Arial', rating_font_size)).pack()

            self.movie_frames.append(frame)

        self.ranking_entry.delete(0, tk.END)
        self.ranking_entry.focus_set()

    def submit_ranking(self):
        ranking = self.ranking_entry.get()
        num_movies = len(self.selected_movies)
        if len(ranking) == 0:
            ranking = "654321"[6-num_movies:6]
        if len(ranking) == num_movies and ranking.isdigit() and set(ranking) == set(map(str, range(1, num_movies + 1))):
            ranking = [int(r) - 1 for r in ranking]
            update_ratings(self.selected_movies, ranking)
            save_csv(self.working_file, self.movies)
            self.total_ranked_count += num_movies
            self.total_ranked_label.config(text=f"Total Ranked: {self.total_ranked_count}")
            self.previous_movies = self.selected_movies
            self.load_new_movies()
        else:
            self.ranking_entry.delete(0, tk.END)
        
        self.ranking_entry.focus_set()

    def undo_last(self):
        if self.previous_movies == None:
            print("Cannot Undo!")
        else:
            for movie in self.selected_movies:
                if movie != new_movie:
                    self.bag.append(movie)
                    self.total_ranked_count -= 1
            self.selected_movies = self.previous_movies
            self.previous_movies = None
            
            num_movies = len(self.selected_movies)
            
            self.total_ranked_label.config(text=f"Total Ranked: {self.total_ranked_count}")

            for frame in self.movie_frames:
                frame.destroy()
            self.movie_frames.clear()

            # Update movies in bag counter
            self.movies_in_bag = len(self.bag)
            self.movies_in_bag_label.config(text=f"Movies in Bag: {self.movies_in_bag}")
            
            # Sort selected movies by their current rating, lowest to highest
            self.selected_movies.sort(key=lambda movie: movie.rating)

            # Calculate dynamic padding and image size based on number of movies
            padx = max(10, int(100 / num_movies))
            img_width = min(200, int(1400 / num_movies))
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

    def quit_app(self):
        compare_csvs(self.original_file, self.working_file, self.diff_file)
        print(f"Changes saved to {self.diff_file}")

        if new_movie:
            with open(self.working_file, 'a', newline='', encoding='utf-8') as working_file:
                writer = csv.writer(working_file)
                writer.writerow([new_movie.date, new_movie.name, new_movie.year, new_movie.uri, new_movie.rating])
            
            with open(self.diff_file, 'a', newline='', encoding='utf-8') as diff_file:
                writer = csv.writer(diff_file)
                writer.writerow([new_movie.date, new_movie.name, new_movie.year, new_movie.uri, new_movie.rating])

        create_working_copy(self.working_file, self.original_file)

        try:
            os.remove(self.working_file)
            print(f"Successfully deleted {self.working_file}")
        except OSError as e:
            print(f"Error deleting {self.working_file}: {e}")

        self.master.quit()
        
def main():
    global mode
    global new_movie
    mode = "3"
    
    new_movie = None
    new_movie_name = None
    new_movie_date = datetime.today().strftime('%Y-%m-%d')
    new_movie_year = 0
    new_movie_rating = 0
    new_movie_uri = None

    while mode not in "12":
        print("Choose operation mode:\n1.) Re-evaluate Existing Ratings\n2.) Rank Newly Watched Film Against Others")
        mode = input()
    if mode == "2":
        print("Enter the movie's title as it appears on Letterboxd:")
        new_movie_name = input()
        print("Enter the movie's release year, according to Letterboxd:")
        new_movie_year = str(validate_year(input()))
        print("Enter the shortened Letterboxd URL for new movie, i.e. 'https://boxd.it/29MQ':")
        new_movie_uri = input()
        print("Enter your initial rating between 0.5 and 5.0")
        new_movie_rating = str(validate_rating(input()))

        
        new_movie = Movie(new_movie_date,new_movie_name,new_movie_year,new_movie_uri,new_movie_rating)
    root = tk.Tk()
    app = MovieRankingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
