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
2. Export and unzip Letterboxd data, then copy your ratings.csv file into the db subfolder.

3. Run snekboxd.py (required packages will be installed automatically):
   ```
   python snekboxd.py
   ```

## Usage

1. The GUI will present you with a series of movies to rank. Enter the numbers corresponding to your preferred order from best to worst (e.g., "31254" for 5 movies, movie #3 being "best" and #4 being "worst").

2. Press Tab or Enter, or click "Submit Ranking" to confirm your ranking and move to the next set of movies.

3. Continue ranking movies until you're satisfied or want to quit.

4. When you quit, a `changed_ratings.csv` file will be generated in the `db` folder, containing only the movies whose ratings have changed as a result of the ranking process.

5. Review the changes and import the `changed_ratings.csv` file back into Letterboxd to update your ratings.

## How it Works

1. snekboxd creates a working copy of your ratings file and shuffles the movies into a "bag."
2. It presents you with a small batch of those movies at a time, fetching posters from TMDB for visual reference. (Note: Fetching can be slow, causing the program to become unresponsive for a couple seconds. But once fetched, the images are saved for future use so they don't need to be fetched again)
3. You rank the presented movies based on your preference.
4. The program adjusts the ratings of the ranked movies to maintain consistency with your choices.
5. This process continues until you decide to quit or have ranked all movies.
6. Upon quitting, snekboxd generates a diff file with only the changed ratings.

## Acknowledgments

- [Letterboxd](https://letterboxd.com/) for providing the movie rating platform
- [TMDB](https://www.themoviedb.org/) for movie poster images

## Disclaimer

This project is not officially affiliated with or endorsed by Letterboxd or TMDB. Use at your own discretion.
