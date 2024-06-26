# snekboxd

A tool for increasing self-consistency among your Letterboxd ratings, in the form of a movie ranking game.

## Description

snekboxd is a Python-based application designed to help Letterboxd users refine and maintain consistency in their movie ratings. By presenting users with a series of movie comparisons, snekboxd allows you to adjust your ratings based on relative preferences, ultimately leading to a more accurate representation of your taste in films without changing your overall rating distributions.

**Note:** This program is intended to leverage Letterboxd's CSV export/import functionality, which is a feature exclusive to Letterboxd Pro members ($19/year subscription).

## Features

- Interactive GUI for easy movie comparison and ranking
- Utilizes your existing Letterboxd ratings
- Fetches movie posters from TMDB for visual reference
- Generates a diff file with changed ratings for easy review and import to Letterboxd

## Requirements

- Python 3.6+
- Letterboxd Pro subscription (for CSV export/import)
- Internet connection (for fetching movie posters)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yaywalter/snekboxd.git
   cd snekboxd
   ```
2. Export and unzip your Letterboxd data, then copy your `ratings.csv` file into the `db` subfolder.

3. Run `snekboxd.py` (Required 3rd party libraries `Pillow`, `requests`, and `BeautifulSoup4` will be installed automatically if missing):
   ```
   python snekboxd.py
   ```
## How It Works & Usage

1. snekboxd creates a working copy of your ratings file and shuffles the movies into a "bag."

2. The GUI presents you with a small batch (typically 5) of movies to rank, fetching posters from TMDB for visual reference. 
   - Note: Fetching can be slow initially, causing the program to become unresponsive for a couple seconds. However, once fetched, the images are saved for future use to speed up subsequent runs.

3. Enter the numbers corresponding to your preferred order from best to worst into the text field (e.g., "31254", where movie #3 is "best" and #4 is "worst").

4. Press Tab or Enter, or click "Submit Ranking" to confirm your ranking and move to the next set of movies.

5. The program adjusts the ratings of the ranked movies to maintain consistency with your choices.

6. Continue ranking movies until you're satisfied or want to quit.

7. When you quit, snekboxd generates a `changed_ratings.csv` file in the `db` folder, containing only the movies whose ratings have changed as a result of the ranking process.

8. Review the changes and import the `changed_ratings.csv` file back into Letterboxd to update your ratings.

## Acknowledgments

- [Letterboxd](https://letterboxd.com/) for providing the movie rating platform
- [TMDB](https://www.themoviedb.org/) for movie poster images

## Disclaimer

This project is not officially affiliated with or endorsed by Letterboxd or TMDB. Use at your own discretion.
