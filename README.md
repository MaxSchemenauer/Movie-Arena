# Active Elo Arena Movie Ranker

A desktop movie ranking app that turns your watchlist into quick one-on-one matchups. Each click updates an Elo-style rating, saves immediately to `movie_rankings.csv`, and refreshes a live leaderboard.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python movie_ranker.py
```

On first launch, the app reads `movies.txt` and creates `movie_rankings.csv`. Replace the sample titles in `movies.txt` with one movie per line before first launch, or delete `movie_rankings.csv` later if you want to rebuild from a new list.

After ranking has started, append new entries to the end of `movies.txt`. The app adds
them on its next launch at 1000 Elo and calibrates only those new movies; do not reorder
the existing lines because their positions are part of their stable local IDs.

To disambiguate a title, use `Title | Year`, for example `Us | 2019`. For remakes
that still share a title and year, use `Title | Year | TMDB ID`. The app stores a
resolved TMDB ID after a successful poster lookup so later downloads stay matched to
that exact movie.

## Posters

Poster fetching is optional. The app works without an API key and shows generated title cards as a fallback.

To enable TMDB posters:

1. Copy `.env.example` to `.env`.
2. Put your key in `.env`:

```text
TMDB_API_KEY=your_real_key
```

Posters are cached in `posters/` and the local path is stored in `movie_rankings.csv`, so each poster only downloads once.

Posters preload automatically in the background when you run `python movie_ranker.py`.
Each downloaded file is saved in `posters/`, so future launches reuse it. The arena only
offers movies whose posters are ready, while any missing posters download in the background.
You never need to run a separate poster script.

## Resetting Rankings

Use the `Reset` button on the leaderboard tab to reset every movie back to `1000` Elo with a `0-0` record. The app asks for confirmation first. Cached posters are kept.

The Arena has `Back` to revisit the immediately preceding matchup. It restores the
previous Elo state when that matchup was voted, or simply restores it when it was
skipped. `Skip` never changes either movie's rating or record.

## Adding Movies

Use the `Add Movies` tab to search TMDB and add an exact title from its results. Each
addition is saved to both `movie_rankings.csv` and `movies.txt`; the selected release
year and TMDB ID keep future poster downloads tied to that movie.

## Data File

`movie_rankings.csv` uses these columns:

```text
id,title,elo_rating,matches_played,wins,losses,poster_local_path
```

The CSV is written after every matchup using an atomic replace, so closing the app mid-session should not lose completed clicks.

## Matchmaking

Each movie is calibrated with three broad comparisons. After that, the arena chooses
nearby ratings within a 100 Elo window, with extra attention to the middle of the
leaderboard. It repeats a close comparison before falling back to a wider gap.
