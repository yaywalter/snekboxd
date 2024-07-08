# Snekboxd

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

1. Download the latest release and unzip.
2. Export your Letterboxd data from [letterboxd.com/settings/data/](https://www.letterboxd.com/settings/data/) (requires Letterboxd Pro) and unzip, then copy your `ratings.csv` file into the `db` subfolder.
3. (Optional) Run `bulk_scrape_posters.py` to scrape all movie poster assets upfront so they don't have to be scraped as you use Snekboxd.
   ```
   python bulk_scrape_posters.py
   ```
4. Run `snekboxd.py` (Required 3rd party libraries `Pillow`, `requests`, and `BeautifulSoup4` will be installed automatically if missing):
   ```
   python snekboxd.py
   ```
## How It Works & Usage
### Mode Selecction
When running Snekboxd, you'll first be asked to choose between one of two modes of operation within the terminal:
1. Re-evaluate Existing Ratings - This mode is for "sanity checking" your pre-existing ratings by asking you to rank groups of films you've seen, automatically swapping the ratings around to match your ranking if they don't already.
2. Rank Newly Watched Film Against Others - This mode is for quickly determining a rating for a newly watched film by repeatedly pitting it against other films you've seen.

### Mode 1: Re-evaluate Existing Ratings
1. snekboxd creates a working copy of your ratings file and shuffles the movies into a "bag."
2. The GUI presents you with a small batch (typically 5) of movies to rank, fetching posters from TMDB for visual reference. 
   - Note: Fetching can be slow initially, causing the program to become unresponsive for a couple seconds. However, once fetched, the images are saved for future use to speed up subsequent runs.
3. Enter the numbers corresponding to your preferred order from best to worst into the text field (e.g., "31254", where movie #3 is "best" and #4 is "worst").
4. Press Tab or Enter, or click "Submit Ranking" to confirm your ranking and move to the next set of movies.
5. The program adjusts the ratings of the ranked movies to maintain consistency with your choices.
6. Continue ranking movies until you're satisfied or want to quit.

### Mode 2: Rank Newly Watched Film Against Others
1. You'll be asked to input the following details into the terminal:
   - Film Title (This should match exactly how it appears on Letterboxd)
   - Release Year (This also should match with the information on Letterboxd)
   - Letterboxd URI (This can be obtained on the film's Letterboxd page in the "Share" section of the side panel, and should look something like `https://boxd.it/gJsA`)
   - Your initial rating (between 0.5 and 5.0)
2. The GUI will present you with comparisons between your new movie and existing rated movies.
3. Rank the new movie against the others as in Mode 1, and the program will use these comparisons to dial in the rating of the new movie.
4. Continue ranking the new movie against others until you're satisfied or want to quit.

### After Using Either Mode
1. When you quit, snekboxd generates a `changed_ratings.csv` file in the `db` folder, containing only the movies whose ratings have changed as a result of the ranking process.
2. Review the changes and import the `changed_ratings.csv` file back into Letterboxd to update your ratings.
3. If you were using Mode 2 to rank a newly watched movie, it is best to log it in your diary *after* uploading `changed_ratings.csv`, that way the rating field will automatically be populated with the correct value.

## Acknowledgments

- [Letterboxd](https://letterboxd.com/) for providing the movie rating platform
- [TMDB](https://www.themoviedb.org/) for movie poster images

## Disclaimer

This project is not officially affiliated with or endorsed by Letterboxd or TMDB. Use at your own discretion.
