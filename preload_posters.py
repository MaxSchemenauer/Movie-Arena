from __future__ import annotations

import csv
import os
from pathlib import Path

import requests
from PIL import Image


APP_DIR = Path(__file__).resolve().parent
CSV_PATH = APP_DIR / "movie_rankings.csv"
POSTER_DIR = APP_DIR / "posters"
ENV_PATH = APP_DIR / ".env"


def main() -> int:
    api_key = read_api_key()
    if not api_key:
        print("No TMDB_API_KEY found. Add one to .env, then run this again.")
        return 1

    if not CSV_PATH.exists():
        print("movie_rankings.csv does not exist yet. Launch movie_ranker.py once first.")
        return 1

    POSTER_DIR.mkdir(exist_ok=True)
    rows = load_rows()
    total = len(rows)
    downloaded = 0
    skipped = 0
    failed: list[str] = []

    for index, row in enumerate(rows, start=1):
        title = row["title"]
        existing_value = row.get("poster_local_path") or ""
        existing_path = Path(existing_value) if existing_value else None
        expected_path = POSTER_DIR / f"{row['id']}.jpg"

        if (existing_path and existing_path.is_file()) or expected_path.is_file():
            row["poster_local_path"] = str(
                existing_path if existing_path and existing_path.is_file() else expected_path
            )
            skipped += 1
            print(f"[{index:03d}/{total}] cached: {title}")
            continue

        try:
            poster_path, tmdb_id = download_poster(
                api_key,
                row["id"],
                title,
                row.get("release_year") or "",
                row.get("tmdb_id") or "",
            )
        except requests.RequestException as exc:
            failed.append(title)
            print(f"[{index:03d}/{total}] failed: {title} ({exc})")
            continue

        if poster_path:
            row["poster_local_path"] = str(poster_path)
            row["tmdb_id"] = tmdb_id
            downloaded += 1
            print(f"[{index:03d}/{total}] downloaded: {title}")
            save_rows(rows)
        else:
            failed.append(title)
            print(f"[{index:03d}/{total}] no poster found: {title}")

    save_rows(rows)
    print()
    print(f"Done. Downloaded {downloaded}, skipped {skipped}, failed/no poster {len(failed)}.")
    if failed:
        print("No poster cached for:")
        for title in failed:
            print(f"  - {title}")
    return 0


def load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def save_rows(rows: list[dict[str, str]]) -> None:
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
    temp_path = CSV_PATH.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, CSV_PATH)


def download_poster(
    api_key: str,
    movie_id: str,
    title: str,
    release_year: str,
    tmdb_id: str,
) -> tuple[Path | None, str]:
    if tmdb_id:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}",
            params={"api_key": api_key},
            timeout=12,
        )
        response.raise_for_status()
        result = response.json()
    else:
        params = {"api_key": api_key, "query": title, "include_adult": "false"}
        if release_year:
            params["year"] = release_year
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params=params,
            timeout=12,
        )
        response.raise_for_status()
        result = next(
            (item for item in response.json().get("results", []) if item.get("poster_path")),
            None,
        )

    if not result:
        return None, ""
    poster_path = result.get("poster_path")
    if not poster_path:
        return None, ""

    image_response = requests.get(f"https://image.tmdb.org/t/p/w780{poster_path}", timeout=20)
    image_response.raise_for_status()

    output_path = POSTER_DIR / f"{movie_id}.jpg"
    output_path.write_bytes(image_response.content)
    verify_image(output_path)
    return output_path, str(result.get("id") or tmdb_id)


def verify_image(path: Path) -> None:
    with Image.open(path) as image:
        image.verify()


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


if __name__ == "__main__":
    raise SystemExit(main())
