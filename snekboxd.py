import csv, os, logging, tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from lib.helper_functions import (
    install, Movie, get_file_md5, download_poster, get_tmdb_poster_url,
    shuffle_deque, sanitize_filename,
    load_csv, save_csv, create_working_copy, create_movie_bag, select_movies,
    update_ratings, compare_csvs, validated_year_input, validated_rating_input,
    validated_uri_input
)

install('Pillow', 'PIL')
from PIL import Image, ImageTk

install('screeninfo')
import screeninfo

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class AppState:
    bag_cycle_count: int = 1
    total_ranked_count: int = 0
    movies_in_bag: int = 0
    selected_movies: List[Movie] = None
    previous_movies: Optional[List[Movie]] = None
    fullscreen: bool = False

class MovieRankingApp:
    def __init__(self, master: tk.Tk, mode, new_movie):
        self.master = master
        self.master.title("Snekboxd")
        
        self.state = AppState()
        self.setup_window()
        self.setup_styles()
        self.setup_file_paths()
        self.load_initial_data()
        self.create_widgets()
        self.setup_bindings()

        self.mode = mode
        self.new_movie = new_movie
        
        self.master.after(100, self.initial_layout)

    def setup_window(self):
        # Get primary monitor information
        monitor = screeninfo.get_monitors()[0]
        
        # Set initial window size to 90% of screen size
        self.window_width = int(monitor.width * 0.9)
        self.window_height = int(monitor.height * 0.9)
        
        # Calculate x and y coordinates for the Tk root window
        x = (monitor.width // 2) - (self.window_width // 2)
        y = (monitor.height // 2) - (self.window_height // 2)
        
        # Set the dimensions of the screen and where it is placed
        self.master.geometry(f'{self.window_width}x{self.window_height}+{x}+{y}')
        self.master.resizable(True, True)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # You can change this to any available theme
        
        # Configure styles for various widgets
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 12))
        style.configure('TButton', font=('Arial', 12))
        style.configure('TEntry', font=('Arial', 12))

    def setup_file_paths(self):
        self.original_file = './db/ratings.csv'
        self.working_file = './db/working_ratings.csv'
        self.diff_file = './db/changed_ratings.csv'
        self.no_image_md5 = get_file_md5('./assets/no_image.jpg')

    def load_initial_data(self):
        create_working_copy(self.original_file, self.working_file)
        self.movies = load_csv(self.working_file)
        self.bag = create_movie_bag(self.movies)
        self.state.movies_in_bag = len(self.bag)
        self.movie_frames = []

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        self.counter_frame = ttk.Frame(self.main_frame)
        self.counter_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)

        self.movies_frame = ttk.Frame(self.main_frame)
        self.movies_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, pady=10)
        self.movies_frame.pack_propagate(False)

        self.create_counter_labels()
        self.create_input_widgets()

    def create_counter_labels(self):
        self.bag_cycle_label = ttk.Label(self.counter_frame, text="Bag Cycles: 1", font=('Arial', 12))
        self.bag_cycle_label.pack(side=tk.LEFT, padx=(0, 20))

        self.total_ranked_label = ttk.Label(self.counter_frame, text="Total Ranked: 0", font=('Arial', 12))
        self.total_ranked_label.pack(side=tk.LEFT, padx=(0, 20))

        self.movies_in_bag_label = ttk.Label(self.counter_frame, text=f"Movies in Bag: {self.state.movies_in_bag}", font=('Arial', 12))
        self.movies_in_bag_label.pack(side=tk.LEFT)

    def create_input_widgets(self):
        self.ranking_entry = ttk.Entry(self.input_frame, font=('Arial', 16), width=10)
        self.ranking_entry.pack(side=tk.LEFT, padx=(0, 20))

        self.submit_button = ttk.Button(self.input_frame, text="Submit Ranking", command=self.submit_ranking, takefocus=0)
        self.submit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.quit_button = ttk.Button(self.input_frame, text="Quit", command=self.quit_app, takefocus=0)
        self.quit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.undo_button = ttk.Button(self.input_frame, text="Undo", command=self.undo_last, takefocus=0)
        self.undo_button.pack(side=tk.LEFT)

    def create_counter_labels(self):
        self.bag_cycle_label = ttk.Label(self.counter_frame, text="Bag Cycles: 1", font=('Arial', 14))
        self.bag_cycle_label.pack(side=tk.LEFT, padx=(0, 20))

        self.total_ranked_label = ttk.Label(self.counter_frame, text="Total Ranked: 0", font=('Arial', 14))
        self.total_ranked_label.pack(side=tk.LEFT, padx=(0, 20))

        self.movies_in_bag_label = ttk.Label(self.counter_frame, text=f"Movies in Bag: {self.state.movies_in_bag}", font=('Arial', 14))
        self.movies_in_bag_label.pack(side=tk.LEFT)

    def create_input_widgets(self):
        self.ranking_entry = ttk.Entry(self.input_frame, font=('Arial', 24), width=10)
        self.ranking_entry.pack(side=tk.LEFT, padx=(0, 20))

        self.submit_button = ttk.Button(self.input_frame, text="Submit Ranking", command=self.submit_ranking, takefocus=0)
        self.submit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.quit_button = ttk.Button(self.input_frame, text="Quit", command=self.quit_app, takefocus=0)
        self.quit_button.pack(side=tk.LEFT, padx=(0, 20))

        self.undo_button = ttk.Button(self.input_frame, text="Undo", command=self.undo_last, takefocus=0)
        self.undo_button.pack(side=tk.LEFT)

    def setup_bindings(self):
        self.master.bind('<Return>', lambda event: self.submit_ranking())
        self.master.bind('<Tab>', lambda event: self.submit_ranking())
        self.master.bind('<Escape>', lambda event: self.quit_app())
        self.master.bind("<Configure>", self.on_resize)
        self.master.protocol("WM_DELETE_WINDOW", self.quit_app)

    def initial_layout(self):
        self.window_width = self.master.winfo_width()
        self.window_height = self.master.winfo_height()
        
        movies_frame_height = int(self.window_height * 0.85)
        self.movies_frame.configure(width=self.window_width - 40, height=movies_frame_height)
        
        self.load_new_movies()

    def on_resize(self, event):
        if event.widget == self.master and not self.state.fullscreen:
            # Get the actual window size
            self.window_width = self.master.winfo_width()
            self.window_height = self.master.winfo_height()
            
            # Update layout
            self.update_layout()

    def update_layout(self):
        if not self.state.selected_movies:
            return

        for frame in self.movie_frames:
            frame.destroy()
        self.movie_frames = []

        num_movies = len(self.state.selected_movies)

        movies_frame_width = self.movies_frame.winfo_width()
        movies_frame_height = self.movies_frame.winfo_height()

        available_width = movies_frame_width - (20 * (num_movies))

        img_width = available_width // num_movies
        img_height = int(img_width * 1.5)

        max_img_height = int(movies_frame_height * 0.85)
        if img_height > max_img_height:
            img_height = max_img_height
            img_width = int(img_height / 1.5)

        for i, movie in enumerate(self.state.selected_movies):
            frame = ttk.Frame(self.movies_frame)
            frame.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 20) if i < num_movies - 1 else 0)

            if movie.image_path:
                img = Image.open(movie.image_path)
                img = img.resize((img_width, img_height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack()

            title_font_size = max(8, min(12, int(img_width / 10)))
            info_font_size = max(6, min(10, int(img_width / 12)))

            ttk.Label(frame, text=f"{movie.name}", wraplength=img_width, font=('Arial', title_font_size)).pack()
            ttk.Label(frame, text=f"({movie.year})", font=('Arial', info_font_size)).pack()
            ttk.Label(frame, text=f"Rating: {movie.rating}", font=('Arial', info_font_size)).pack()

            self.movie_frames.append(frame)

    def load_new_movies(self):
        for frame in self.movie_frames:
            frame.destroy()
        self.movie_frames = []

        if len(self.bag) < 2:
            if len(self.bag) > 0:
                self.bag.popleft()
            self.bag.extend(self.movies)
            shuffle_deque(self.bag)
            self.state.bag_cycle_count += 1
            self.bag_cycle_label.config(text=f"Bag Cycles: {self.state.bag_cycle_count}")

        num_movies = min(5, len(self.bag))
        self.state.selected_movies = select_movies(self.bag, num_movies)

        if self.mode == "2" and self.new_movie not in self.state.selected_movies:
            self.state.selected_movies.append(self.new_movie)

        self.fetch_missing_posters()

        self.state.movies_in_bag = len(self.bag)
        self.movies_in_bag_label.config(text=f"Movies in Bag: {self.state.movies_in_bag}")
        
        self.state.selected_movies.sort(key=lambda movie: movie.rating)

        self.update_layout()

        self.ranking_entry.delete(0, tk.END)
        self.ranking_entry.focus_set()

    def fetch_missing_posters(self):
        for movie in self.state.selected_movies:
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

    def submit_ranking(self):
        ranking = self.ranking_entry.get()
        num_movies = len(self.state.selected_movies)
        if len(ranking) == 0:
            ranking = "654321"[6-num_movies:6]
        if len(ranking) == num_movies and ranking.isdigit() and set(ranking) == set(map(str, range(1, num_movies + 1))):
            ranking = [int(r) - 1 for r in ranking]
            update_ratings(self.state.selected_movies, ranking)
            save_csv(self.working_file, self.movies)
            self.state.total_ranked_count += num_movies
            self.total_ranked_label.config(text=f"Total Ranked: {self.state.total_ranked_count}")
            self.state.previous_movies = self.state.selected_movies
            self.load_new_movies()
        else:
            self.ranking_entry.delete(0, tk.END)
        
        self.ranking_entry.focus_set()

    def undo_last(self):
        if self.state.previous_movies is None:
            print("Cannot Undo!")
        else:
            for movie in self.state.selected_movies:
                if movie != self.new_movie:
                    self.bag.append(movie)
                    self.state.total_ranked_count -= 1
            self.state.selected_movies = self.state.previous_movies
            self.state.previous_movies = None
            
            self.total_ranked_label.config(text=f"Total Ranked: {self.state.total_ranked_count}")

            self.state.movies_in_bag = len(self.bag)
            self.movies_in_bag_label.config(text=f"Movies in Bag: {self.state.movies_in_bag}")
            
            self.state.selected_movies.sort(key=lambda movie: movie.rating)

            self.update_layout()

            self.ranking_entry.delete(0, tk.END)
            self.ranking_entry.focus_set()

    def quit_app(self):
        compare_csvs(self.original_file, self.working_file, self.diff_file)
        print(f"Changes saved to {self.diff_file}")

        if self.new_movie:
            new_movie = self.new_movie
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

def get_new_movie_info():
    confirmed = False
    while not confirmed:
        print("Enter the movie's title as it appears on Letterboxd:")
        name = input()
        year = validated_year_input("Enter the movie's release year, according to Letterboxd:")
        uri = validated_uri_input("Enter the shortened Letterboxd URL for new movie, i.e. 'https://boxd.it/29MQ':")
        rating = validated_rating_input("Enter your initial rating between 0.5 and 5.0")
        print(f"\nYou entered the following:\n{name = }\n{year = }\n{uri = }\n{rating = }\n\nProceed? Y/N")
        confirmed = True if input().lower() in ["yes","1","true","proceed","sure","ok","yeah, baby!","y"] else False
        print("")
    
    return Movie(
        date=datetime.today().strftime('%Y-%m-%d'),
        name=name,
        year=year,
        uri=uri,
        rating=rating
    )

def get_operation_mode() -> str:
    while True:
        print("Choose operation mode:")
        print("1.) Re-evaluate Existing Ratings")
        print("2.) Rank Newly Watched Film Against Others")
        mode = input()
        if mode in ["1", "2"]:
            return mode
        print("Invalid input. Please enter 1 or 2.")

def main():
    mode = get_operation_mode()
    new_movie = get_new_movie_info() if mode == "2" else None

    root = tk.Tk()
    app = MovieRankingApp(root, mode, new_movie)
    
    root.mainloop()

if __name__ == "__main__":
    main()
