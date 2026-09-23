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

## Momentum And Re-evaluation

- [ ] Add a rolling momentum signal based on recent unexpected Elo gains or losses, not simply consecutive wins. A new movie that beats stronger nearby movies can earn a temporary upward challenge path; a falling movie can receive a downward one.
- [ ] Momentum should expand the normal Elo window selectively toward stronger or weaker opponents, then fade once the movie starts producing ordinary expected results and re-settles.
- [ ] Add exposure guardrails: cooldowns, opponent diversity, and a short-window repeat limit so a rising or falling movie is not shown over and over.
- [ ] Slightly increase the chance of a momentum matchup, but do not let it dominate the arena queue or starve the rest of the roster.
- [ ] Make re-evaluation explicit in the movie detail view: show that a movie is moving quickly because recent results conflict with its established rating.

## Graphs And Persistent History

- [ ] Use chronological time as the default graph axis, shared across every selected movie.
- [ ] Compress only globally inactive intervals with an explicitly marked broken-time segment such as "6 days with no votes"; never compress an interval containing any matchup event. This keeps cross-movie graphs aligned without wasting space on inactivity.
- [ ] Allow a matchup-count axis as an optional diagnostic view, while keeping time as the comparison-friendly default.
- [ ] Preserve compact matchup events permanently. Each event should contain only the participants, selected winner or tie, Elo/rank before and after, algorithm version, and timestamp.
- [ ] Build graph tooltips and movie logs from those events rather than storing repeated full-leaderboard snapshots.

## Rating Tiers And Algorithm Releases

- [ ] Keep ordinal rank (number 1, number 2, and so on) separate from optional presentation tiers. Elo orders the current roster; a badge should never obscure that exact order.
- [ ] Do not force a fixed percentage of movies into Bronze, Platinum, or Supersonic Legend. A personal list of favorites may honestly contain no low-tier movie or many high-tier movies.
- [ ] For personal rankings, prefer user-local descriptive bands or configurable fixed thresholds, and label them as personal rather than universal competitive skill tiers.
- [ ] Reserve globally calibrated competitive-style tiers for a future shared pool with enough cross-user data, stable thresholds, and published methodology.
- [ ] For a ranking-algorithm release, support three migration modes: continue with current Elo going forward, replay the saved matchup events under the new algorithm, or start a clearly labeled new season seeded from prior ratings rather than flat-resetting every movie.
- [ ] Version tier thresholds and ranking rules alongside matchup events so charts and historical explanations remain interpretable after patches.

## Local Profiles And Portable Data

- [ ] Create a local profile on first startup, with its own movie list, leaderboard, matchup events, posters, and settings stored outside the code repository and ignored by Git.
- [ ] Seed new profiles from an optional default movie list, then let each person diverge completely.
- [ ] Use an explicit profile chooser or local profile name, not computer fingerprinting. Hardware identity is fragile, confusing on shared devices, and a poor foundation for future sign-in.
- [ ] Later, link an authenticated account to a profile for backup and cross-device sync without mixing personal leaderboards by accident.
- [ ] Add profile export/import so a person can move their list between computers without publishing private rankings.

## Global Ranking Confidence

- [ ] Give every global movie a coverage report: number of distinct users, number of distinct opponent relationships, genre/franchise diversity, and uncertainty.
- [ ] Treat repeated choices of the same pair by one person as revisions or sharply decayed evidence, not unlimited additional wins and losses.
- [ ] Cap each person's total global influence before considering diversity. Do not simply reward people with broad portfolios by giving them unlimited voting power.
- [ ] Down-weight narrow comparison islands for a general global ranking while preserving them as valid signals in genre, franchise, or community-specific rankings.
- [ ] Detect bridge movies and bridge users that connect otherwise separate taste clusters; these comparisons are especially valuable for estimating a coherent broader ranking.
- [ ] Publish confidence beside any global position so a highly rated movie with mostly superhero-only exposure is visibly less certain than one tested across many audiences and opponent types.
- [ ] maybe the more comparisions and movies a users movie subset has gives it more weight, but with diminishing return. 

## Social And Fun

- [ ] Share a read-only ranking page or export a polished image of the top 10.
- [ ] Create separate rankings for different people, then compare their lists.
- [ ] Group mode where several people vote and the app aggregates their preferences.
- [ ] Theme packs based on genres, studios, or film eras.
- [ ] End-of-year recap: most compared films, biggest risers, and final top 10.
