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
- [ ] Persist one compact matchup event per vote: movie, opponent, result, Elo before/after, rank before/after, and timestamp. Do not store a full leaderboard snapshot after every vote.
- [ ] Compare a movie directly against its nearest neighbors on demand.

## Leaderboard Tools

- [ ] Search the leaderboard and jump directly to a movie.
- [ ] Filter by calibrated, uncalibrated, recently added, or a rating range.
- [ ] Sort by win percentage, placement progress, date added, or recent activity.
  Rank and Elo are the same ordering, so they should not be separate sort modes.
- [ ] Show persistent rank movement over a chosen time or matchup range; do not frame the product around sessions.
- [ ] Reset one movie to 1000 Elo and `0 / 3` placement matches.
- [ ] Remove a movie with a confirmation dialog and an option to preserve its matchup
  history in an archive.
- [ ] Add a details view with poster, rating graph, wins, losses, and comparison log.
- [ ] Movie history view: list every matchup, its opponent, result, Elo change, and
  the rating immediately after that vote.
- [ ] Interactive Elo-over-time graph for one or several selected movies. Hovering a point should reveal the opponent, outcome, Elo delta, rank delta, and timestamp.
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
- [ ] Non-blocking result panel: after a vote, animate only the changed Elo and rank in a compact side panel while the next matchup is already ready to click. It may use color, arrows, and a short count-up, but must never add an artificial wait.
- [ ] Modern arena redesign: establish a polished visual system, faster transitions, strong poster presentation, restrained light effects, and clear hierarchy. Evaluate a web UI when the interaction and animation needs outgrow CustomTkinter.


## Matchmaking Philosophy

- [ ] Replace hidden middle weighting with an explicit exposure policy. Default toward near-uniform sampling after calibration, then use uncertainty and nearby Elo to choose high-information matchups.
- [ ] Optionally add a mild top-half bias only if data shows the highest ranks are under-tested; expose the rationale and coverage metrics.
- [ ] Preserve the smooth global order: a direct winner should not be automatically forced above the direct loser. A head-to-head upset is strong evidence, especially for a new movie, but it should be balanced against the rest of both movies' records.
- [ ] Let a surprising recent preference accelerate a movie's re-evaluation by scheduling several nearby high-information opponents, rather than imposing a brittle one-match rank override.
- [ ] Show matchup coverage and opponent diversity so the user can see whether a movie's rating rests on broad evidence or a narrow set of repeated rivals.

## Personal, Shared, And Global Rankings

- [ ] Keep every personal leaderboard private and internally consistent; global ranking must be a separate aggregate, never a replacement for someone's taste.
- [ ] Aggregate pairwise preferences, not raw win/loss totals. A repeated Odyssey-versus-Interstellar vote from one small ten-movie roster must have sharply diminishing weight.
- [ ] Count each user-pair relationship with a cap or decay, then normalize a user's total contribution so large and small personal rosters have fair influence.
- [ ] Use the overlap between users' movie lists to connect preference communities, and report uncertainty when a title lacks comparisons across different audiences.
- [ ] Separate stable consensus from niche preference: support global, community, genre, and friend-group views rather than pretending there is one unquestionable ranking.
- [ ] Store immutable matchup events and version every aggregate algorithm. Ranking patches should recompute derived scores without discarding the original preferences.
- [ ] Add authentication, rate limits, anti-bot controls, and repeat-vote rules before any public aggregate is trusted.

## Platform And Metadata Strategy

- [ ] Treat TMDB as a development-time metadata provider, not an assumed commercial asset source. Review its current terms and image attribution/licensing before any public or commercial launch.
- [ ] Put movie metadata and poster retrieval behind a provider adapter so the application is not structurally tied to TMDB.
- [ ] Research licensed, open, public-domain, user-supplied, and paid artwork options; avoid bulk scraping or mirroring a third-party poster catalog.
- [ ] Define a first-class stable item model now: local item ID, external provider IDs, title, year, and media provenance. It can later support movies, books, games, music, and other pairwise-ranked domains.
## Social And Fun

- [ ] Share a read-only ranking page or export a polished image of the top 10.
- [ ] Create separate rankings for different people, then compare their lists.
- [ ] Group mode where several people vote and the app aggregates their preferences.
- [ ] Theme packs based on genres, studios, or film eras.
- [ ] End-of-year recap: most compared films, biggest risers, and final top 10.
