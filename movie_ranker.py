from __future__ import annotations

import csv
import json
import math
import os
import random
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable

import customtkinter as ctk
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps


APP_DIR = Path(__file__).resolve().parent
CSV_PATH = APP_DIR / "movie_rankings.csv"
MOVIES_TXT_PATH = APP_DIR / "movies.txt"
POSTER_DIR = APP_DIR / "posters"
ENV_PATH = APP_DIR / ".env"
HISTORY_PATH = APP_DIR / "ranking_history.json"

STARTING_ELO = 1000.0
POSTER_SIZE = (360, 540)
SEARCH_POSTER_SIZE = (74, 111)
PLACEMENT_MATCH_TARGET = 3
RECENT_MOVIE_LIMIT = 8
NORMAL_MATCHUP_ELO_WINDOW = 100.0


@dataclass
class MovieSpec:
    title: str
    release_year: str = ""
    tmdb_id: str = ""


@dataclass
class MovieSearchResult:
    tmdb_id: str
    title: str
    release_year: str
    overview: str
    poster_path: str = ""


@dataclass
class Movie:
    id: str
    title: str
    release_year: str = ""
    tmdb_id: str = ""
    elo_rating: float = STARTING_ELO
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    poster_local_path: str = ""

    @property
    def display_title(self) -> str:
        return f"{self.title} ({self.release_year})" if self.release_year else self.title

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Movie":
        return cls(
            id=row["id"],
            title=row["title"],
            release_year=row.get("release_year") or "",
            tmdb_id=row.get("tmdb_id") or "",
            elo_rating=float(row.get("elo_rating") or STARTING_ELO),
            matches_played=int(row.get("matches_played") or 0),
            wins=int(row.get("wins") or 0),
            losses=int(row.get("losses") or 0),
            poster_local_path=row.get("poster_local_path") or "",
        )

    def to_row(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "release_year": self.release_year,
            "tmdb_id": self.tmdb_id,
            "elo_rating": f"{self.elo_rating:.2f}",
            "matches_played": str(self.matches_played),
            "wins": str(self.wins),
            "losses": str(self.losses),
            "poster_local_path": self.poster_local_path,
        }


class MovieStore:
    fieldnames = [
        "id",
        "title",
        "release_year",
        "tmdb_id",
        "elo_rating",
        "matches_played",
        "wins",
        "losses",
        "poster_local_path",
    ]

    def __init__(self, csv_path: Path, movies_txt_path: Path) -> None:
        self.csv_path = csv_path
        self.movies_txt_path = movies_txt_path
        self._lock = threading.RLock()
        self.movies: list[Movie] = []
        self.load_or_initialize()

    def load_or_initialize(self) -> None:
        with self._lock:
            if self.csv_path.exists():
                self.movies, needs_save = self._load_csv()
                if self._sync_movie_metadata():
                    needs_save = True
                if needs_save:
                    self.save()
                self._write_movies_txt()
                return

            specs = self._load_movie_specs()
            self.movies = [
                Movie(
                    id=f"{index:04d}-{slugify(spec.title) or 'movie'}",
                    title=spec.title,
                    release_year=spec.release_year,
                    tmdb_id=spec.tmdb_id,
                )
                for index, spec in enumerate(specs, start=1)
            ]
            self.save()
            self._write_movies_txt()

    def _load_movie_specs(self) -> list["MovieSpec"]:
        if not self.movies_txt_path.exists():
            raise FileNotFoundError(
                f"Missing {self.movies_txt_path.name}. Add one movie title per line."
            )

        specs = [
            parse_movie_spec(line)
            for line in self.movies_txt_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if len(specs) < 2:
            raise ValueError("movies.txt needs at least two movie titles.")
        return specs

    def _load_csv(self) -> tuple[list[Movie], bool]:
        with self.csv_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            csv_fieldnames = set(reader.fieldnames or [])
            optional_fields = {"release_year", "tmdb_id"}
            missing = (set(self.fieldnames) - optional_fields) - csv_fieldnames
            if missing:
                raise ValueError(
                    f"{self.csv_path.name} is missing columns: {', '.join(sorted(missing))}"
                )
            movies = [Movie.from_row(row) for row in reader]
        if len(movies) < 2:
            raise ValueError(f"{self.csv_path.name} needs at least two movies.")
        return movies, not optional_fields.issubset(csv_fieldnames)

    def _sync_movie_metadata(self) -> bool:
        changed = False
        specs = self._load_movie_specs()
        for index, spec in enumerate(specs, start=1):
            movie_id = f"{index:04d}-{slugify(spec.title) or 'movie'}"
            try:
                movie = self.by_id(movie_id)
            except KeyError:
                if index > len(self.movies):
                    self.movies.append(
                        Movie(
                            id=movie_id,
                            title=spec.title,
                            release_year=spec.release_year,
                            tmdb_id=spec.tmdb_id,
                        )
                    )
                    changed = True
                continue
            if spec.release_year and movie.release_year != spec.release_year:
                movie.release_year = spec.release_year
                if not movie.tmdb_id:
                    cached_path = POSTER_DIR / f"{movie.id}.jpg"
                    if cached_path.is_file():
                        cached_path.unlink()
                    movie.poster_local_path = ""
                changed = True
            if spec.tmdb_id and movie.tmdb_id != spec.tmdb_id:
                movie.tmdb_id = spec.tmdb_id
                cached_path = POSTER_DIR / f"{movie.id}.jpg"
                if cached_path.is_file():
                    cached_path.unlink()
                movie.poster_local_path = ""
                changed = True
        return changed

    def _write_movies_txt(self) -> None:
        lines = [format_movie_spec(movie) for movie in self.movies]
        contents = "\n".join(lines) + "\n"
        current = (
            self.movies_txt_path.read_text(encoding="utf-8")
            if self.movies_txt_path.exists()
            else ""
        )
        if current != contents:
            self.movies_txt_path.write_text(contents, encoding="utf-8")

    def add_movie(
        self, title: str, release_year: str, tmdb_id: str
    ) -> tuple[Movie, bool]:
        with self._lock:
            existing = next(
                (movie for movie in self.movies if tmdb_id and movie.tmdb_id == tmdb_id),
                None,
            )
            if existing:
                return existing, False

            movie = Movie(
                id=self._next_movie_id(title),
                title=title,
                release_year=release_year,
                tmdb_id=tmdb_id,
            )
            self.movies.append(movie)
            self.save()
            self._write_movies_txt()
            return movie, True

    def has_tmdb_id(self, tmdb_id: str) -> bool:
        with self._lock:
            return any(movie.tmdb_id == tmdb_id for movie in self.movies)

    def _next_movie_id(self, title: str) -> str:
        numbers = [
            int(movie.id.split("-", 1)[0])
            for movie in self.movies
            if movie.id.split("-", 1)[0].isdigit()
        ]
        return f"{max(numbers, default=0) + 1:04d}-{slugify(title) or 'movie'}"

    def save(self) -> None:
        with self._lock:
            temp_path = self.csv_path.with_name(
                f"{self.csv_path.stem}.{threading.get_ident()}.tmp"
            )
            with temp_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
                for movie in self.movies:
                    writer.writerow(movie.to_row())

            retry_delays = (0, 0.05, 0.1, 0.2, 0.4, 0.8)
            for attempt, delay in enumerate(retry_delays):
                if delay:
                    time.sleep(delay)
                try:
                    os.replace(temp_path, self.csv_path)
                    self._write_movies_txt()
                    return
                except PermissionError:
                    if attempt == len(retry_delays) - 1:
                        raise

    def by_id(self, movie_id: str) -> Movie:
        with self._lock:
            for movie in self.movies:
                if movie.id == movie_id:
                    return movie
        raise KeyError(movie_id)

    def sorted_movies(self) -> list[Movie]:
        with self._lock:
            return sorted(self.movies, key=lambda movie: movie.elo_rating, reverse=True)

    def update_poster_path(
        self, movie_id: str, poster_path: Path, persist: bool = True
    ) -> None:
        with self._lock:
            self.by_id(movie_id).poster_local_path = str(poster_path)
            if persist:
                self.save()

    def update_poster_details(
        self, movie_id: str, poster_path: Path, tmdb_id: str, persist: bool = True
    ) -> None:
        with self._lock:
            movie = self.by_id(movie_id)
            movie.poster_local_path = str(poster_path)
            if tmdb_id:
                movie.tmdb_id = tmdb_id
            if persist:
                self.save()

    def rating_snapshots(self, movie_ids: tuple[str, str]) -> list[dict[str, object]]:
        with self._lock:
            snapshots: list[dict[str, object]] = []
            for movie_id in movie_ids:
                movie = self.by_id(movie_id)
                snapshots.append(
                    {
                        "id": movie.id,
                        "elo_rating": movie.elo_rating,
                        "matches_played": movie.matches_played,
                        "wins": movie.wins,
                        "losses": movie.losses,
                    }
                )
            return snapshots

    def restore_rating_snapshots(self, snapshots: list[dict[str, object]]) -> None:
        with self._lock:
            for snapshot in snapshots:
                movie = self.by_id(str(snapshot["id"]))
                movie.elo_rating = float(snapshot["elo_rating"])
                movie.matches_played = int(snapshot["matches_played"])
                movie.wins = int(snapshot["wins"])
                movie.losses = int(snapshot["losses"])
            self.save()

    def record_result(self, winner_id: str, loser_id: str) -> tuple[Movie, Movie]:
        with self._lock:
            winner = self.by_id(winner_id)
            loser = self.by_id(loser_id)

            winner_expected = expected_score(winner.elo_rating, loser.elo_rating)
            loser_expected = expected_score(loser.elo_rating, winner.elo_rating)
            winner_k = k_factor(winner.matches_played)
            loser_k = k_factor(loser.matches_played)

            winner.elo_rating += winner_k * (1 - winner_expected)
            loser.elo_rating += loser_k * (0 - loser_expected)
            winner.matches_played += 1
            loser.matches_played += 1
            winner.wins += 1
            loser.losses += 1

            self.save()
            return winner, loser

    def reset_rankings(self) -> None:
        with self._lock:
            for movie in self.movies:
                movie.elo_rating = STARTING_ELO
                movie.matches_played = 0
                movie.wins = 0
                movie.losses = 0
            self.save()


class RankingHistory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.records = self._load()

    def has_entries(self) -> bool:
        return bool(self.records)

    def push(self, record: dict[str, object]) -> None:
        self.records.append(record)
        self._save()

    def pop(self) -> dict[str, object] | None:
        if not self.records:
            return None
        record = self.records.pop()
        self._save()
        return record

    def clear(self) -> None:
        self.records = []
        self._save()

    def _load(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return payload if isinstance(payload, list) else []

    def _save(self) -> None:
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self.records), encoding="utf-8")
        os.replace(temp_path, self.path)


class Matchmaker:
    def __init__(self, store: MovieStore) -> None:
        self.store = store
        self.session_pairs: set[tuple[str, str]] = set()
        self.recent_movie_ids: deque[str] = deque(maxlen=RECENT_MOVIE_LIMIT)

    def next_pair(self, eligible_ids: set[str] | None = None) -> tuple[Movie, Movie]:
        movies = list(self.store.movies)
        if eligible_ids is not None:
            movies = [movie for movie in movies if movie.id in eligible_ids]
        if len(movies) < 2:
            raise ValueError("At least two movies are required.")

        pair = self._calibration_pair(movies) or self._coverage_pair(movies)
        self._remember_pair(pair[0].id, pair[1].id)
        return pair

    def _calibration_pair(self, movies: list[Movie]) -> tuple[Movie, Movie] | None:
        unfinished = [
            movie
            for movie in movies
            if movie.matches_played < PLACEMENT_MATCH_TARGET
        ]
        if not unfinished:
            return None

        lowest_count = min(movie.matches_played for movie in unfinished)
        first_pool = [
            movie for movie in unfinished if movie.matches_played == lowest_count
        ]
        first = self._choose_movie(first_pool, prefer_not_recent=True)

        second_pool = [
            movie
            for movie in unfinished
            if movie.id != first.id and movie.matches_played == lowest_count
        ]
        if not second_pool:
            remaining = [movie for movie in movies if movie.id != first.id]
            next_count = min(movie.matches_played for movie in remaining)
            second_pool = [
                movie
                for movie in remaining
                if movie.matches_played == next_count
            ]

        second = self._choose_opponent(first, second_pool, prefer_not_recent=True)
        return first, second

    def _coverage_pair(self, movies: list[Movie]) -> tuple[Movie, Movie]:
        anchor = self._choose_coverage_anchor(movies)
        rivals = self._nearby_rivals(anchor, movies)

        if not rivals:
            # A long session can exhaust local unseen pairs. Allow a repeat before
            # widening the rating window, preserving local comparison quality.
            self.session_pairs.clear()
            rivals = self._nearby_rivals(anchor, movies)

        if not rivals:
            rivals = [
                movie
                for movie in movies
                if movie.id != anchor.id and not self._has_seen(anchor.id, movie.id)
            ]
        if not rivals:
            self.session_pairs.clear()
            rivals = [movie for movie in movies if movie.id != anchor.id]

        return anchor, self._choose_coverage_rival(anchor, rivals)

    def _choose_coverage_anchor(self, movies: list[Movie]) -> Movie:
        minimum_matches = min(movie.matches_played for movie in movies)
        least_exposed = [
            movie for movie in movies if movie.matches_played == minimum_matches
        ]
        return self._choose_movie(least_exposed, prefer_not_recent=True)

    def _nearby_rivals(self, anchor: Movie, movies: list[Movie]) -> list[Movie]:
        return [
            movie
            for movie in movies
            if movie.id != anchor.id
            and abs(movie.elo_rating - anchor.elo_rating) <= NORMAL_MATCHUP_ELO_WINDOW
            and not self._has_seen(anchor.id, movie.id)
        ]

    def _choose_coverage_rival(self, anchor: Movie, rivals: list[Movie]) -> Movie:
        candidates = self._without_recent(rivals)
        minimum_matches = min(movie.matches_played for movie in candidates)
        weights = []
        for movie in candidates:
            elo_distance = abs(movie.elo_rating - anchor.elo_rating)
            closeness = 1 - (elo_distance / NORMAL_MATCHUP_ELO_WINDOW)
            coverage = 1 / (1 + max(0, movie.matches_played - minimum_matches))
            weights.append((0.2 + closeness) * coverage)
        return random.choices(candidates, weights=weights, k=1)[0]

    def _choose_movie(
        self, candidates: list[Movie], *, prefer_not_recent: bool
    ) -> Movie:
        choices = self._without_recent(candidates) if prefer_not_recent else candidates
        return random.choice(choices)

    def _choose_opponent(
        self, anchor: Movie, candidates: list[Movie], *, prefer_not_recent: bool
    ) -> Movie:
        unseen = [
            movie for movie in candidates if not self._has_seen(anchor.id, movie.id)
        ]
        choices = unseen or candidates
        if prefer_not_recent:
            choices = self._without_recent(choices)
        return random.choice(choices)

    def _without_recent(self, movies: list[Movie]) -> list[Movie]:
        recent_ids = set(self.recent_movie_ids)
        fresh = [movie for movie in movies if movie.id not in recent_ids]
        return fresh or movies

    def _remember_pair(self, first_id: str, second_id: str) -> None:
        self.session_pairs.add(pair_key(first_id, second_id))
        self.recent_movie_ids.extend((first_id, second_id))

    def _has_seen(self, first_id: str, second_id: str) -> bool:
        return pair_key(first_id, second_id) in self.session_pairs

class PosterService:
    def __init__(self, store: MovieStore, api_key: str) -> None:
        self.store = store
        self.api_key = api_key
        self._in_flight: set[str] = set()
        self._preloading = False
        self._image_cache: dict[str, Image.Image] = {}
        self._fallback_cache: dict[str, Image.Image] = {}
        self._lock = threading.Lock()
        POSTER_DIR.mkdir(exist_ok=True)

    def image_for_movie(
        self,
        movie: Movie,
        on_loaded: Callable[[str, Image.Image], None],
    ) -> Image.Image:
        with self._lock:
            cached_image = self._image_cache.get(movie.id)
            if cached_image:
                return cached_image

        local_path = Path(movie.poster_local_path) if movie.poster_local_path else None
        expected_path = POSTER_DIR / f"{movie.id}.jpg"
        if not is_poster_file(local_path):
            local_path = None
        if local_path is None and expected_path.is_file():
            local_path = expected_path
            self.store.update_poster_path(movie.id, expected_path)
        if local_path:
            try:
                image = load_poster(local_path)
            except OSError:
                image = self._fallback_for(movie)
            else:
                with self._lock:
                    self._image_cache[movie.id] = image
            return image

        fallback = self._fallback_for(movie)
        if self.api_key and not self._preloading:
            self._fetch_async(movie, on_loaded)
        return fallback

    def preload_all(
        self,
        on_loaded: Callable[[str, Image.Image], None],
        on_progress: Callable[[int, int, int], None],
    ) -> None:
        self._preloading = True
        thread = threading.Thread(
            target=self._run_preload,
            args=(on_loaded, on_progress),
            daemon=True,
        )
        thread.start()

    def ready_movie_ids(self) -> set[str]:
        with self._lock:
            return set(self._image_cache)

    def fetch_movie_async(
        self, movie: Movie, on_loaded: Callable[[str, Image.Image], None]
    ) -> None:
        if self.api_key:
            self._fetch_async(movie, on_loaded)

    def _run_preload(
        self,
        on_loaded: Callable[[str, Image.Image], None],
        on_progress: Callable[[int, int, int], None],
    ) -> None:
        try:
            self._preload_worker(on_loaded, on_progress)
        finally:
            self._preloading = False

    def _preload_worker(
        self,
        on_loaded: Callable[[str, Image.Image], None],
        on_progress: Callable[[int, int, int], None],
    ) -> None:
        movies = list(self.store.movies)
        total = len(movies)
        cached_count = 0
        poster_metadata_changed = False

        for completed, movie in enumerate(movies, start=1):
            with self._lock:
                cached_image = self._image_cache.get(movie.id)

            if cached_image:
                cached_count += 1
                on_progress(completed, total, cached_count)
                continue

            local_path = Path(movie.poster_local_path) if movie.poster_local_path else None
            expected_path = POSTER_DIR / f"{movie.id}.jpg"
            if not is_poster_file(local_path):
                local_path = None
            if local_path is None and expected_path.is_file():
                local_path = expected_path
                self.store.update_poster_path(movie.id, expected_path, persist=False)
                poster_metadata_changed = True

            if local_path and movie.tmdb_id:
                try:
                    image = load_poster(local_path)
                except OSError:
                    image = None
                if image:
                    with self._lock:
                        self._image_cache[movie.id] = image
                    on_loaded(movie.id, image)
                    cached_count += 1
                on_progress(completed, total, cached_count)
                continue

            if not self.api_key:
                on_progress(completed, total, cached_count)
                continue

            with self._lock:
                if movie.id in self._in_flight:
                    on_progress(completed, total, cached_count)
                    continue
                self._in_flight.add(movie.id)

            try:
                try:
                    poster_path, tmdb_id = self._download_poster(movie)
                except requests.RequestException:
                    poster_path, tmdb_id = None, ""

                if poster_path:
                    try:
                        image = load_poster(poster_path)
                    except OSError:
                        image = None
                    if image:
                        with self._lock:
                            self._image_cache[movie.id] = image
                        self.store.update_poster_details(
                            movie.id, poster_path, tmdb_id, persist=False
                        )
                        poster_metadata_changed = True
                        on_loaded(movie.id, image)
                        cached_count += 1
                elif local_path:
                    try:
                        image = load_poster(local_path)
                    except OSError:
                        image = None
                    if image:
                        with self._lock:
                            self._image_cache[movie.id] = image
                        on_loaded(movie.id, image)
                        cached_count += 1
            finally:
                with self._lock:
                    self._in_flight.discard(movie.id)
                on_progress(completed, total, cached_count)

        if poster_metadata_changed:
            try:
                self.store.save()
            except PermissionError:
                # A later normal save can persist these cache paths; the poster files
                # remain available through their predictable filenames.
                pass

    def _fallback_for(self, movie: Movie) -> Image.Image:
        with self._lock:
            cached_fallback = self._fallback_cache.get(movie.id)
            if cached_fallback:
                return cached_fallback

        image = fallback_poster(movie.title)
        with self._lock:
            self._fallback_cache[movie.id] = image
        return image

    def _fetch_async(
        self,
        movie: Movie,
        on_loaded: Callable[[str, Image.Image], None],
    ) -> None:
        with self._lock:
            if movie.id in self._in_flight:
                return
            self._in_flight.add(movie.id)

        thread = threading.Thread(
            target=self._fetch_worker,
            args=(movie, on_loaded),
            daemon=True,
        )
        thread.start()

    def _fetch_worker(
        self,
        movie: Movie,
        on_loaded: Callable[[str, Image.Image], None],
    ) -> None:
        try:
            try:
                poster_path, tmdb_id = self._download_poster(movie)
            except requests.RequestException:
                poster_path, tmdb_id = None, ""

            if poster_path:
                try:
                    image = load_poster(poster_path)
                except OSError:
                    return
                with self._lock:
                    self._image_cache[movie.id] = image
                self.store.update_poster_details(movie.id, poster_path, tmdb_id)
                on_loaded(movie.id, image)
        finally:
            with self._lock:
                self._in_flight.discard(movie.id)

    def _download_poster(self, movie: Movie) -> tuple[Path | None, str]:
        if movie.tmdb_id:
            response = requests.get(
                f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}",
                params={"api_key": self.api_key},
                timeout=12,
            )
            response.raise_for_status()
            result = response.json()
        else:
            params = {
                "api_key": self.api_key,
                "query": movie.title,
                "include_adult": "false",
            }
            if movie.release_year:
                params["year"] = movie.release_year
            response = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params=params,
                timeout=12,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            normalized_title = normalize_movie_title(movie.title)
            exact_results = [
                item
                for item in results
                if item.get("poster_path")
                and normalize_movie_title(
                    item.get("title") or item.get("original_title") or ""
                )
                == normalized_title
                and (
                    not movie.release_year
                    or (item.get("release_date") or "")[:4] == movie.release_year
                )
            ]
            result = exact_results[0] if len(exact_results) == 1 else None

        if not result:
            return None, ""
        poster_path = result.get("poster_path")
        if not poster_path:
            return None, ""

        poster_url = f"https://image.tmdb.org/t/p/w780{poster_path}"
        image_response = requests.get(poster_url, timeout=20)
        image_response.raise_for_status()

        output_path = POSTER_DIR / f"{movie.id}.jpg"
        output_path.write_bytes(image_response.content)
        return output_path, str(result.get("id") or movie.tmdb_id)


class MovieRankerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Active Elo Arena")
        self.geometry("1180x960")
        self.minsize(980, 860)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.store = MovieStore(CSV_PATH, MOVIES_TXT_PATH)
        self.history = RankingHistory(HISTORY_PATH)
        self.matchmaker = Matchmaker(self.store)
        api_key = read_api_key()
        self.poster_api_enabled = bool(api_key)
        self.poster_service = PosterService(self.store, api_key)
        self.current_pair: tuple[Movie, Movie] | None = None
        self.input_locked = False
        self.leaderboard_rows: list[tuple[ctk.CTkFrame, list[ctk.CTkLabel]]] = []
        self._search_after_id: str | None = None
        self._search_request_id = 0
        self._search_images: dict[str, ctk.CTkImage] = {}

        self._ctk_images: dict[str, ctk.CTkImage] = {}
        self._build_ui()
        if not self.poster_api_enabled:
            self.poster_status_label.configure(
                text="No TMDB_API_KEY found in .env; only already-saved posters are available."
            )
        self.poster_service.preload_all(self._poster_loaded, self._poster_preload_progress)
        self.load_next_matchup()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tabs.grid(row=0, column=0, padx=18, pady=18, sticky="nsew")
        self.arena_tab = self.tabs.add("Arena")
        self.leaderboard_tab = self.tabs.add("Leaderboard")
        self.add_movies_tab = self.tabs.add("Add Movies")

        self._build_arena()
        self._build_leaderboard()
        self._build_add_movies()

    def _build_arena(self) -> None:
        self.arena_tab.grid_columnconfigure(0, weight=1, uniform="arena")
        self.arena_tab.grid_columnconfigure(1, weight=0)
        self.arena_tab.grid_columnconfigure(2, weight=1, uniform="arena")
        self.arena_tab.grid_rowconfigure(0, weight=1)
        self.arena_tab.grid_rowconfigure(1, weight=0)

        self.left_card = MovieCard(self.arena_tab, self.choose_left)
        self.left_card.grid(row=0, column=0, padx=(24, 14), pady=24, sticky="nsew")

        center = ctk.CTkFrame(self.arena_tab, fg_color="transparent", width=96)
        center.grid(row=0, column=1, sticky="ns")
        center.grid_rowconfigure(0, weight=1)
        center.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            center,
            text="VS",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#8ea4bd",
        ).grid(row=1, column=0)

        self.right_card = MovieCard(self.arena_tab, self.choose_right)
        self.right_card.grid(row=0, column=2, padx=(14, 24), pady=24, sticky="nsew")

        self.status_label = ctk.CTkLabel(
            self.arena_tab,
            text="",
            text_color="#8ea4bd",
            font=ctk.CTkFont(size=14),
        )
        self.status_label.grid(row=1, column=0, columnspan=3, pady=(0, 18), sticky="ew")

        controls = ctk.CTkFrame(self.arena_tab, fg_color="transparent")
        controls.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        self.back_button = ctk.CTkButton(
            controls,
            text="Back",
            width=100,
            command=self.undo_last_choice,
        )
        self.back_button.grid(row=0, column=0, padx=(0, 10))
        ctk.CTkButton(
            controls,
            text="Skip",
            width=100,
            fg_color="#334155",
            hover_color="#475569",
            command=self.skip_matchup,
        ).grid(row=0, column=1)
        self._update_history_controls()

        self.poster_status_label = ctk.CTkLabel(
            self.arena_tab,
            text="Preparing poster cache...",
            text_color="#64788f",
            font=ctk.CTkFont(size=12),
        )
        self.poster_status_label.grid(
            row=3, column=0, columnspan=3, pady=(0, 12), sticky="ew"
        )

    def _build_leaderboard(self) -> None:
        self.leaderboard_tab.grid_columnconfigure(0, weight=1)
        self.leaderboard_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.leaderboard_tab, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(22, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Leaderboard",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            header,
            text="Reset",
            width=92,
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            command=self.confirm_reset_leaderboard,
        ).grid(row=0, column=1, sticky="e")

        self.leaderboard_frame = ctk.CTkScrollableFrame(self.leaderboard_tab)
        self.leaderboard_frame.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="nsew")
        for column, weight in enumerate((0, 1, 0, 0)):
            self.leaderboard_frame.grid_columnconfigure(column, weight=weight)
        self.refresh_leaderboard()

    def _build_add_movies(self) -> None:
        self.add_movies_tab.grid_columnconfigure(0, weight=1)
        self.add_movies_tab.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self.add_movies_tab, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(22, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Add Movies",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.movie_search_entry = ctk.CTkEntry(
            self.add_movies_tab,
            placeholder_text="Search for a movie...",
            height=42,
            font=ctk.CTkFont(size=16),
        )
        self.movie_search_entry.grid(row=1, column=0, padx=24, sticky="ew")
        self.movie_search_entry.bind("<KeyRelease>", self._schedule_movie_search)
        self.movie_search_entry.bind("<Return>", self._search_now)

        self.movie_search_status = ctk.CTkLabel(
            self.add_movies_tab,
            text=(
                "Start typing to search TMDB."
                if self.poster_api_enabled
                else "Add a TMDB_API_KEY to .env to search for movies."
            ),
            text_color="#8ea4bd",
            anchor="w",
        )
        self.movie_search_status.grid(row=2, column=0, padx=24, pady=(10, 4), sticky="new")

        self.movie_search_results = ctk.CTkScrollableFrame(self.add_movies_tab)
        self.movie_search_results.grid(row=3, column=0, padx=24, pady=(0, 24), sticky="nsew")
        self.movie_search_results.grid_columnconfigure(0, weight=1)

    def _schedule_movie_search(self, _event: object | None = None) -> None:
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_request_id += 1
        query = self.movie_search_entry.get().strip()
        if len(query) < 2:
            self._clear_search_results()
            self.movie_search_status.configure(text="Type at least two characters to search.")
            return
        self.movie_search_status.configure(text="Searching...")
        request_id = self._search_request_id
        self._search_after_id = self.after(
            300, lambda: self._run_movie_search(query, request_id)
        )

    def _search_now(self, _event: object | None = None) -> None:
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_request_id += 1
        query = self.movie_search_entry.get().strip()
        if len(query) >= 2:
            self._run_movie_search(query, self._search_request_id)

    def _run_movie_search(self, query: str, request_id: int) -> None:
        self._search_after_id = None
        if not self.poster_api_enabled:
            return
        thread = threading.Thread(
            target=self._movie_search_worker,
            args=(query, request_id),
            daemon=True,
        )
        thread.start()

    def _movie_search_worker(self, query: str, request_id: int) -> None:
        try:
            response = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={
                    "api_key": self.poster_service.api_key,
                    "query": query,
                    "include_adult": "false",
                },
                timeout=12,
            )
            response.raise_for_status()
            results = [
                MovieSearchResult(
                    tmdb_id=str(item["id"]),
                    title=item.get("title") or item.get("original_title") or "Untitled",
                    release_year=(item.get("release_date") or "")[:4],
                    overview=item.get("overview") or "No overview available.",
                    poster_path=item.get("poster_path") or "",
                )
                for item in response.json().get("results", [])[:8]
                if item.get("id")
            ]
            error = ""
        except (requests.RequestException, ValueError):
            results = []
            error = "Search failed. Check your TMDB key and connection."

        self.after(0, lambda: self._render_movie_search(request_id, results, error))

    def _render_movie_search(
        self,
        request_id: int,
        results: list[MovieSearchResult],
        error: str,
    ) -> None:
        if request_id != self._search_request_id:
            return
        self._clear_search_results()
        if error:
            self.movie_search_status.configure(text=error)
            return
        if not results:
            self.movie_search_status.configure(text="No movies found.")
            return

        self.movie_search_status.configure(text=f"{len(results)} results")
        for result in results:
            self._add_search_result_row(result)

    def _clear_search_results(self) -> None:
        for widget in self.movie_search_results.winfo_children():
            widget.destroy()
        self._search_images.clear()

    def _add_search_result_row(self, result: MovieSearchResult) -> None:
        row = ctk.CTkFrame(self.movie_search_results, corner_radius=6, fg_color="#17212d")
        row.pack(fill="x", padx=4, pady=5)
        row.grid_columnconfigure(1, weight=1)

        poster_label = ctk.CTkLabel(row, text="", width=SEARCH_POSTER_SIZE[0], height=SEARCH_POSTER_SIZE[1])
        poster_label.grid(row=0, column=0, rowspan=2, padx=12, pady=12, sticky="n")

        title = result.title
        if result.release_year:
            title = f"{title} ({result.release_year})"
        ctk.CTkLabel(
            row,
            text=title,
            anchor="w",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=1, padx=(0, 12), pady=(14, 2), sticky="ew")
        ctk.CTkLabel(
            row,
            text=result.overview,
            anchor="w",
            justify="left",
            wraplength=560,
            text_color="#aebdca",
        ).grid(row=1, column=1, padx=(0, 12), pady=(0, 14), sticky="new")

        already_added = self.store.has_tmdb_id(result.tmdb_id)
        ctk.CTkButton(
            row,
            text="Added" if already_added else "Add",
            width=82,
            state="disabled" if already_added else "normal",
            command=lambda item=result: self._add_search_result(item),
        ).grid(row=0, column=2, rowspan=2, padx=(0, 14), pady=14, sticky="e")

        if result.poster_path:
            self._load_search_thumbnail(result, poster_label)

    def _load_search_thumbnail(
        self, result: MovieSearchResult, poster_label: ctk.CTkLabel
    ) -> None:
        thread = threading.Thread(
            target=self._search_thumbnail_worker,
            args=(result, poster_label),
            daemon=True,
        )
        thread.start()

    def _search_thumbnail_worker(
        self, result: MovieSearchResult, poster_label: ctk.CTkLabel
    ) -> None:
        try:
            response = requests.get(
                f"https://image.tmdb.org/t/p/w185{result.poster_path}", timeout=12
            )
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGB")
            image = ImageOps.fit(image, SEARCH_POSTER_SIZE, method=Image.Resampling.LANCZOS)
        except (OSError, requests.RequestException):
            return

        def apply_thumbnail() -> None:
            if not poster_label.winfo_exists():
                return
            thumbnail = ctk.CTkImage(
                light_image=image, dark_image=image, size=SEARCH_POSTER_SIZE
            )
            self._search_images[result.tmdb_id] = thumbnail
            poster_label.configure(image=thumbnail)
            poster_label.image = thumbnail

        self.after(0, apply_thumbnail)

    def _add_search_result(self, result: MovieSearchResult) -> None:
        movie, added = self.store.add_movie(
            result.title, result.release_year, result.tmdb_id
        )
        if not added:
            self.movie_search_status.configure(text=f"{movie.display_title} is already in your list.")
            return

        self.poster_service.fetch_movie_async(movie, self._poster_loaded)
        self.movie_search_status.configure(
            text=f"Added {movie.display_title}. Its poster is downloading in the background."
        )
        self.refresh_leaderboard()
        self._schedule_movie_search()

    def _on_tab_change(self) -> None:
        if self.tabs.get() == "Leaderboard":
            self.refresh_leaderboard()

    def choose_left(self) -> None:
        self.record_choice(0)

    def choose_right(self) -> None:
        self.record_choice(1)

    def record_choice(self, winner_index: int) -> None:
        if self.input_locked or self.current_pair is None:
            return

        self.input_locked = True
        left, right = self.current_pair
        winner = self.current_pair[winner_index]
        loser = self.current_pair[1 - winner_index]
        snapshots = self.store.rating_snapshots((winner.id, loser.id))
        updated_winner, updated_loser = self.store.record_result(winner.id, loser.id)
        self.history.push(
            {
                "kind": "vote",
                "left_id": left.id,
                "right_id": right.id,
                "snapshots": snapshots,
            }
        )
        self._update_history_controls()
        self.status_label.configure(
            text=(
                f"{updated_winner.title} wins: {updated_winner.elo_rating:.0f} "
                f"| {updated_loser.title}: {updated_loser.elo_rating:.0f}"
            )
        )
        if self.tabs.get() == "Leaderboard":
            self.refresh_leaderboard()
        self.after(10, self.load_next_matchup)

    def skip_matchup(self) -> None:
        if self.input_locked or self.current_pair is None:
            return
        self.input_locked = True
        left, right = self.current_pair
        self.history.push(
            {
                "kind": "skip",
                "left_id": left.id,
                "right_id": right.id,
            }
        )
        self._update_history_controls()
        self.status_label.configure(text="Matchup skipped.")
        self.after(10, self.load_next_matchup)

    def undo_last_choice(self) -> None:
        record = self.history.pop()
        if not record:
            return

        try:
            left = self.store.by_id(str(record["left_id"]))
            right = self.store.by_id(str(record["right_id"]))
            is_vote = record.get("kind", "vote") == "vote"
            if is_vote:
                snapshots = record["snapshots"]
                if not isinstance(snapshots, list):
                    raise ValueError("Missing rating snapshots")
                self.store.restore_rating_snapshots(snapshots)
        except (KeyError, TypeError, ValueError):
            self.status_label.configure(text="Could not restore that previous matchup.")
            self._update_history_controls()
            return

        self.current_pair = (left, right)
        self._set_card(self.left_card, left)
        self._set_card(self.right_card, right)
        self.input_locked = False
        self.status_label.configure(
            text="Previous choice undone. Choose this matchup again."
            if is_vote
            else "Skipped matchup restored."
        )
        self._update_history_controls()
        if self.tabs.get() == "Leaderboard":
            self.refresh_leaderboard()

    def _update_history_controls(self) -> None:
        self.back_button.configure(state="normal" if self.history.has_entries() else "disabled")

    def load_next_matchup(self) -> None:
        ready_ids = self.poster_service.ready_movie_ids()
        if len(ready_ids) < 2:
            self.current_pair = None
            self.input_locked = True
            self.left_card.set_pending()
            self.right_card.set_pending()
            if self.poster_api_enabled:
                self.status_label.configure(text="Preparing the first poster matchups...")
                self.after(100, self.load_next_matchup)
            else:
                self.status_label.configure(
                    text="Add a TMDB_API_KEY to .env to download posters and begin ranking."
                )
            return

        self.current_pair = self.matchmaker.next_pair(ready_ids)
        left, right = self.current_pair
        self._set_card(self.left_card, left)
        self._set_card(self.right_card, right)
        self.input_locked = False

    def _set_card(self, card: "MovieCard", movie: Movie) -> None:
        image = self.poster_service.image_for_movie(movie, self._poster_loaded)
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=POSTER_SIZE)
        self._ctk_images[movie.id] = ctk_image
        card.set_movie(movie, ctk_image)

    def _poster_loaded(self, movie_id: str, image: Image.Image) -> None:
        def apply_if_visible() -> None:
            if self.current_pair:
                left, right = self.current_pair
            else:
                left = right = None
            if left and left.id == movie_id:
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=POSTER_SIZE)
                self._ctk_images[movie_id] = ctk_image
                self.left_card.set_image(ctk_image)
            elif right and right.id == movie_id:
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=POSTER_SIZE)
                self._ctk_images[movie_id] = ctk_image
                self.right_card.set_image(ctk_image)

        self.after(0, apply_if_visible)

    def _poster_preload_progress(
        self, completed: int, total: int, cached_count: int
    ) -> None:
        def update_status() -> None:
            if completed >= total:
                suffix = "" if self.poster_api_enabled else " (add a TMDB key for missing posters)"
                self.poster_status_label.configure(
                    text=f"Posters ready: {cached_count}/{total} cached{suffix}"
                )
            else:
                self.poster_status_label.configure(
                    text=f"Preparing posters: {completed}/{total}"
                )

        self.after(0, update_status)

    def refresh_leaderboard(self) -> None:
        movies = self.store.sorted_movies()
        self._ensure_leaderboard_rows(len(movies))
        gold_cutoff = max(1, math.ceil(len(movies) * 0.10))
        silver_cutoff = max(gold_cutoff + 1, math.ceil(len(movies) * 0.30))

        for index, movie in enumerate(movies, start=1):
            text_color = "#f4c95d" if index <= gold_cutoff else "#c7d0d9"
            if gold_cutoff < index <= silver_cutoff:
                text_color = "#d5dde5"
            row, labels = self.leaderboard_rows[index - 1]
            row.configure(fg_color="#17212d" if index % 2 else "#121a24")

            values = (
                str(index),
                movie.display_title,
                f"{movie.elo_rating:.0f}",
                f"{movie.wins}-{movie.losses}",
            )
            for column, value in enumerate(values):
                labels[column].configure(
                    text=value,
                    text_color=text_color,
                    font=ctk.CTkFont(size=15, weight="bold" if index <= gold_cutoff else "normal"),
                )

    def _ensure_leaderboard_rows(self, movie_count: int) -> None:
        if not self.leaderboard_frame.winfo_children():
            headers = ("Rank", "Title", "Elo", "W-L")
            for column, text in enumerate(headers):
                anchor = "w" if column == 1 else "center"
                ctk.CTkLabel(
                    self.leaderboard_frame,
                    text=text,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#8ea4bd",
                    anchor=anchor,
                ).grid(row=0, column=column, padx=10, pady=(8, 10), sticky="ew")

        while len(self.leaderboard_rows) < movie_count:
            index = len(self.leaderboard_rows) + 1
            row = ctk.CTkFrame(self.leaderboard_frame, fg_color="#17212d", corner_radius=6)
            row.grid(row=index, column=0, columnspan=4, padx=4, pady=3, sticky="ew")
            row.grid_columnconfigure(1, weight=1)

            labels: list[ctk.CTkLabel] = []
            for column in range(4):
                anchor = "w" if column == 1 else "center"
                width = 70 if column != 1 else 520
                label = ctk.CTkLabel(
                    row,
                    text="",
                    width=width,
                    anchor=anchor,
                    text_color="#c7d0d9",
                    font=ctk.CTkFont(size=15),
                )
                label.grid(row=0, column=column, padx=10, pady=9, sticky="ew")
                labels.append(label)
            self.leaderboard_rows.append((row, labels))

        while len(self.leaderboard_rows) > movie_count:
            row, _labels = self.leaderboard_rows.pop()
            row.destroy()

    def confirm_reset_leaderboard(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Reset leaderboard?")
        dialog.geometry("460x220")
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="Reset every rating, win, loss, and match count?",
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=380,
        ).grid(row=0, column=0, padx=28, pady=(28, 8), sticky="ew")
        ctk.CTkLabel(
            dialog,
            text="Poster downloads stay cached. Ranking history will be overwritten immediately.",
            text_color="#8ea4bd",
            wraplength=380,
        ).grid(row=1, column=0, padx=28, pady=(0, 24), sticky="ew")

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.grid(row=2, column=0, padx=28, pady=(0, 28), sticky="e")
        ctk.CTkButton(actions, text="Cancel", width=92, command=dialog.destroy).grid(
            row=0, column=0, padx=(0, 10)
        )
        ctk.CTkButton(
            actions,
            text="Yes, Reset",
            width=118,
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            command=lambda: self.reset_leaderboard(dialog),
        ).grid(row=0, column=1)

    def reset_leaderboard(self, dialog: ctk.CTkToplevel) -> None:
        dialog.destroy()
        self.input_locked = True
        self.store.reset_rankings()
        self.history.clear()
        self._update_history_controls()
        self.matchmaker = Matchmaker(self.store)
        self.status_label.configure(text="Leaderboard reset to 1000 Elo.")
        self.refresh_leaderboard()
        self.load_next_matchup()


class MovieCard(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, command: Callable[[], None]) -> None:
        super().__init__(
            master,
            corner_radius=18,
            border_width=2,
            border_color="#26364a",
            fg_color="#101823",
        )
        self.command = command
        self.default_border = "#26364a"
        self.hover_border = "#3d8bfd"
        self.movie: Movie | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.poster_label = ctk.CTkLabel(self, text="")
        self.poster_label.grid(row=0, column=0, padx=20, pady=(22, 14), sticky="s")

        self.title_label = ctk.CTkLabel(
            self,
            text="",
            wraplength=380,
            justify="center",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=1, column=0, padx=22, pady=(0, 8), sticky="ew")

        self.meta_label = ctk.CTkLabel(
            self,
            text="",
            text_color="#8ea4bd",
            font=ctk.CTkFont(size=14),
        )
        self.meta_label.grid(row=2, column=0, padx=22, pady=(0, 22), sticky="ew")

        for widget in (self, self.poster_label, self.title_label, self.meta_label):
            widget.bind("<Button-1>", self._clicked)
            widget.bind("<Enter>", self._hover_on)
            widget.bind("<Leave>", self._hover_off)

    def set_movie(self, movie: Movie, image: ctk.CTkImage) -> None:
        self.movie = movie
        self.set_image(image)
        self.title_label.configure(text=movie.display_title)
        self.meta_label.configure(
            text=f"Elo {movie.elo_rating:.0f}  |  {movie.wins}-{movie.losses}"
        )

    def set_pending(self) -> None:
        self.movie = None
        self.poster_label.configure(image=None, text="")
        self.poster_label.image = None
        self.title_label.configure(text="Preparing posters")
        self.meta_label.configure(text="Your first matchup is almost ready")

    def set_image(self, image: ctk.CTkImage) -> None:
        self.poster_label.configure(image=image)
        self.poster_label.image = image

    def _clicked(self, _event: object) -> None:
        self.command()

    def _hover_on(self, _event: object) -> None:
        self.configure(border_color=self.hover_border, fg_color="#121d2a")

    def _hover_off(self, _event: object) -> None:
        self.configure(border_color=self.default_border, fg_color="#101823")


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def k_factor(matches_played: int) -> int:
    return 40 if matches_played < 10 else 20


def pair_key(first_id: str, second_id: str) -> tuple[str, str]:
    return tuple(sorted((first_id, second_id)))


def normalize_movie_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48]


def parse_movie_spec(line: str) -> MovieSpec:
    parts = [part.strip() for part in line.split("|")]
    title = parts[0]
    if not title:
        raise ValueError("Each movie entry needs a title.")
    release_year = parts[1] if len(parts) > 1 else ""
    tmdb_id = parts[2] if len(parts) > 2 else ""
    if release_year and not re.fullmatch(r"\d{4}", release_year):
        raise ValueError(f"Invalid release year for {title}: {release_year}")
    if tmdb_id and not tmdb_id.isdigit():
        raise ValueError(f"Invalid TMDB ID for {title}: {tmdb_id}")
    if len(parts) > 3:
        raise ValueError(f"Too many fields for {title}. Use Title | Year | TMDB ID.")
    return MovieSpec(title=title, release_year=release_year, tmdb_id=tmdb_id)


def format_movie_spec(movie: Movie) -> str:
    if movie.tmdb_id:
        return f"{movie.title} | {movie.release_year} | {movie.tmdb_id}"
    if movie.release_year:
        return f"{movie.title} | {movie.release_year}"
    return movie.title


def read_api_key() -> str:
    env_key = os.environ.get("TMDB_API_KEY", "").strip()
    if env_key:
        return env_key

    if not ENV_PATH.exists():
        return ""

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        if key.strip() == "TMDB_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def load_poster(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return ImageOps.fit(image, POSTER_SIZE, method=Image.Resampling.LANCZOS)


def is_poster_file(path: Path | None) -> bool:
    return path is not None and path.is_file()


def fallback_poster(title: str) -> Image.Image:
    image = Image.new("RGB", POSTER_SIZE, "#17212d")
    draw = ImageDraw.Draw(image)

    for y in range(POSTER_SIZE[1]):
        shade = 28 + int(y / POSTER_SIZE[1] * 28)
        draw.line((0, y, POSTER_SIZE[0], y), fill=(shade, 38, 52))

    draw.rounded_rectangle(
        (18, 18, POSTER_SIZE[0] - 18, POSTER_SIZE[1] - 18),
        radius=24,
        outline="#3d8bfd",
        width=3,
    )

    title_font = font(size=34, bold=True)
    small_font = font(size=16, bold=False)
    lines = wrap_text(draw, title.upper(), title_font, POSTER_SIZE[0] - 70)
    total_height = len(lines) * 42
    y = (POSTER_SIZE[1] - total_height) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        x = (POSTER_SIZE[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill="#eef5ff", font=title_font)
        y += 42

    footer = "NO POSTER"
    footer_bbox = draw.textbbox((0, 0), footer, font=small_font)
    draw.text(
        ((POSTER_SIZE[0] - (footer_bbox[2] - footer_bbox[0])) // 2, POSTER_SIZE[1] - 58),
        footer,
        fill="#8ea4bd",
        font=small_font,
    )
    return image


def font(size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["segoeuib.ttf", "segoeui.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    image_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=image_font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines or [text]


def main() -> None:
    try:
        app = MovieRankerApp()
    except Exception as exc:
        show_startup_error(exc)
        return
    app.mainloop()


def show_startup_error(exc: Exception) -> None:
    ctk.set_appearance_mode("dark")
    window = ctk.CTk()
    window.title("Active Elo Arena")
    window.geometry("620x260")
    window.grid_columnconfigure(0, weight=1)
    message = (
        "The movie ranker could not start.\n\n"
        f"{exc}\n\n"
        "Check movies.txt or movie_rankings.csv, then launch again."
    )
    ctk.CTkLabel(
        window,
        text=message,
        justify="left",
        wraplength=540,
        font=ctk.CTkFont(size=16),
    ).grid(row=0, column=0, padx=32, pady=32, sticky="nsew")
    ctk.CTkButton(window, text="Close", command=window.destroy).grid(
        row=1, column=0, padx=32, pady=(0, 28), sticky="e"
    )
    window.mainloop()


if __name__ == "__main__":
    main()
