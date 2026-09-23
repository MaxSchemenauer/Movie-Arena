# Movie Ranker Feature Backlog

This is a product backlog, not a commitment list. Items near the top resolve the
most important ranking and data-management needs first.

## Ranking Quality

- [ ] Fair calibration scheduler: always pair two movies with the fewest placement
  matches, so every movie gets its first comparison before any movie receives a
  fourth one.
- [ ] Calibration target control: choose 3, 5, or a custom number of initial matches.
- [ ] Show calibration progress per movie, such as `2 / 3 placement matches`.
- [ ] Add a `Tie / Cannot choose` result that records uncertainty without treating it
  as a skip.
- [ ] Show confidence beside each rank; early rankings should look provisional.
- [ ] Let the user choose strictness for normal Elo matchmaking, such as a 50, 100,
  or 150-point window.
- [ ] Track strength of schedule so a movie cannot climb mainly through weak opponents.
- [ ] Add a temporary `re-evaluate` mode for movies whose rank feels stale.
- [ ] Record matchup history and show why a movie's Elo changed.
- [ ] Compare a movie directly against its nearest neighbors on demand.

## Leaderboard Tools

- [ ] Search the leaderboard and jump directly to a movie.
- [ ] Filter by calibrated, uncalibrated, recently added, or a rating range.
- [ ] Sort by rank, Elo, win percentage, placement progress, or date added.
- [ ] Show rank movement since the previous session.
- [ ] Reset one movie to 1000 Elo and `0 / 3` placement matches.
- [ ] Remove a movie with a confirmation dialog and an option to preserve its matchup
  history in an archive.
- [ ] Add a details view with poster, rating graph, wins, losses, and comparison log.
- [ ] Pin favorites or create custom watchlist tags.

## Discovery And Bulk Add

- [ ] Search a director, actor, writer, or studio and show the full filmography, not
  only the first eight search results.
- [ ] Bulk selection: poster grid, `Select all`, per-movie checkboxes, and one `Add
  selected` action.
- [ ] Apply filters to a person search: directing credits only, feature films only,
  release-year range, minimum runtime, and exclude shorts or documentaries.
- [ ] Franchise and collection browser powered by TMDB collections where available.
- [ ] Curated franchise builders for broader universes that are not one TMDB
  collection, such as MCU phases, Star Wars eras, James Bond, or Studio Ghibli.
- [ ] Bulk add from a decade, genre, country, production company, awards list, or
  a saved TMDB list.
- [ ] Preview duplicates before bulk add and choose whether to skip, merge, or keep
  distinct versions.
- [ ] Add a "poster is wrong" action that searches alternatives and lets you select
  the correct TMDB result.

## Data And Reliability

- [ ] Automatic timestamped backups before resets, removals, and bulk operations.
- [ ] Import and export CSV/JSON backups, including ratings and matchup history.
- [ ] Import watchlists and ratings from Letterboxd, IMDb, Trakt, or a plain CSV.
- [ ] Data health screen for missing posters, duplicate titles, invalid metadata, and
  movies that still need placement matches.
- [ ] Optional cloud backup or Git-based version history for the local database.
- [ ] Portable single-file distribution for Windows, so Python setup is unnecessary.
- [ ] Add a local web version for browser access while keeping the same local data.

## Arena Experience

- [ ] Keyboard controls for left, right, skip, back, and tie.
- [ ] Fullscreen comparison mode with larger posters.
- [ ] Optional movie metadata under each poster: year, director, runtime, genre, and
  a short synopsis.
- [ ] Toggle to hide ratings during voting to reduce anchoring bias.
- [ ] Matchup queue showing the next few comparisons without revealing both choices
  too early.
- [ ] Lightweight animations and better loading states for poster downloads.
- [ ] Accessibility pass: high contrast, scalable text, keyboard navigation, and
  screen-reader labels.
- [ ] animation where both movie flip around, then reveal their current position and elo, then you see the winning movie's elo turn green if it moves up, with a green up arrow, and the points smoothly increase, the losing movie's points turn red and decrease, and the rank slides up or down as well, or stays the same (depending on where it moves to of course). this should be quick, or even literally on the side, so the next matchup can get there right away. users will hate having to wait even 500ms if they dont have to. Maybe there is a side panel that shows the animation / update from the previous match?
- [ ] big ui upgrade to be smoother and modern, more pretty, good colors / light effects / diffused gradient stuff, less tkinter gui vibes. (maybe this needs the web upgrade, or a stronger engine)

## Social And Fun

- [ ] Share a read-only ranking page or export a polished image of the top 10.
- [ ] Create separate rankings for different people, then compare their lists.
- [ ] Group mode where several people vote and the app aggregates their preferences.
- [ ] Theme packs based on genres, studios, or film eras.
- [ ] End-of-year recap: most compared films, biggest risers, and final top 10.
