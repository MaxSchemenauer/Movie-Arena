# Proposed Movie Ranker Features

This document organizes the backlog into named feature proposals. A proposal is a
coherent deliverable, not necessarily a single small task. The wording preserves the
original ideas while grouping them by the user-facing capability they create.

## Core Ranking

### Fair Placement Calibration

**Goal:** Give every newly added movie an even, understandable starting process.

- Pair two movies from the lowest placement-match count so every movie receives its
  first comparison before any receives a fourth.
- Let the user choose a placement target of 3, 5, or a custom number of matches.
- Show clear progress such as 2 / 3 placement matches.
- Mark early rankings as provisional and show rating confidence.

### Match Outcome Options

**Goal:** Capture more honest preferences than a forced win or a skip.

- Add Tie / Cannot choose as a result that records uncertainty without becoming a skip.
- Keep Skip as no ranking signal at all.
- Support direct compare against a movie's nearest neighbors on demand.

### Coverage-Aware Matchmaking

**Goal:** Make normal match selection feel fair, smooth, and explainable.

- Replace hidden middle weighting with an explicit exposure policy.
- Default toward near-uniform movie exposure after calibration, then choose nearby-Elo,
  high-information matchups.
- Offer normal Elo-window strictness such as 50, 100, or 150 points.
- Permit a mild top-half bias only when coverage data shows those ranks are
  under-tested, and show the rationale.
- Track matchup coverage, opponent diversity, comparison counts, and strength of
  schedule so a movie cannot climb mostly through weak or repeated opponents.
- Show whether a rating rests on broad evidence or a narrow comparison island.

### Momentum Re-evaluation

**Goal:** Let a movie that is clearly misplaced move quickly without making the arena
repetitive or forcing a brittle one-match rank override.

- Detect rolling momentum from recent unexpected Elo gains or losses, not simply
  consecutive wins.
- Give a rising movie a temporary upward challenge path and a falling movie a
  temporary downward challenge path.
- Selectively widen and shift its opponent window in the correct direction: a rising
  movie gets mostly-higher challenges, while a falling movie gets mostly-lower ones.
### Historical Schedule Re-evaluation

**Goal:** Correct the opportunity to prove a movie's placement when early pairings turn
out, in retrospect, to have been unusually easy or unusually hard, without granting
free Elo or making permanent complexity out of a warm-up problem.

- Periodically estimate a movie's retrospective strength of schedule after later
  results make its past opponents more informative.
- Compare its historical opponents' current or stabilized strength with the strength
  normally faced by movies at a similar current rank and evidence level.
- Detect both possible placement-luck patterns: a strong movie initially brutalized by
  eventual top favorites, and a high-ranked movie built mostly against eventual weaker
  opponents.
- Discount the signal when few comparisons exist and taper it as broad, diverse
  evidence accumulates; ordinary long-run matchmaking should increasingly be fair on
  its own.
- Use the signal to schedule targeted, high-information re-evaluation matchups in the
  direction that tests the suspicious placement, rather than changing Elo
  retrospectively.
- For example, a movie that later proves to have lost only to the user's top three can
  receive stronger-than-its-current-rank challenges and earn a rapid recovery by
  winning them.
- Combine historical schedule luck with momentum, rewatch-driven preference changes,
  new-entry calibration, confidence, cooldowns, and opponent diversity, while keeping
  the total policy deliberately small and explainable.
- Use simulations to verify that this intervention improves recovery and does not
  create persistent bias, over-scheduling, or a system that cannot eventually settle.
- Add cooldowns, opponent diversity, and short-window repeat limits so the same movie
  does not appear too often.
- Slightly increase momentum-match likelihood without starving the rest of the roster.
- Fade the boost when outcomes become ordinary and the movie re-settles.
- Show in the movie detail view that a rating is moving quickly because recent
  preferences conflict with its established position.

### Rating-Engine Stability And Simulation

**Goal:** Tune rating changes and matchmaking from measurable behavior rather than
guessing at Elo windows, K-factors, or a preferred rating distribution.

- Keep ordinary Elo point changes dependent on the Elo gap, not ordinal rank: expected
  wins produce small changes and upsets produce larger ones.
- Use one shared, pairwise K-factor for both participants so a simple Elo matchup is
  zero-sum even when the movies have different amounts of prior evidence.
- Evaluate whether new or uncertain movies need a temporary higher shared K-factor,
  while avoiding unexplained rating-pool inflation or deflation.
- Treat the eventual Elo spread as an observed property of the user's preferences and
  comparison graph, not a fixed target or an artificially enforced distribution.
- Build a deterministic simulation harness that runs the real matchmaker through
  100, 1,000, 2,000, and 3,000 synthetic votes.
- Test smooth transitive preferences, a favorites-heavy pool with a long high-quality
  tail, intransitive preferences, changed opinions after a rewatch, and late additions.
- Measure coverage fairness, Elo spread, top-rank recovery, rank stability, calibration
  speed, and the ability of a genuinely misplaced movie to re-settle.

### Smooth Head-to-Head Policy

**Goal:** Respect direct results without destroying the meaning of the full ranking.

- Do not automatically force a direct winner above the direct loser.
- Treat an upset, especially by a new movie, as strong evidence that produces a
  meaningful Elo move and useful follow-up matchups.
- Balance it against each movie's broader record, avoiding a hard rank swap that breaks
  smoothness and creates awkward head-to-head implications.

## Movie History And Insight

### Compact Matchup Event Ledger

**Goal:** Preserve the information needed for explanations, graphs, future algorithm
updates, and global aggregation without saving full leaderboard snapshots.

- Persist one compact event for each vote: participants, winner or tie, Elo and rank
  before/after, algorithm version, and timestamp.
- Build movie logs, explanations, and charts from those events.
- Do not store a complete leaderboard snapshot after every vote.

### Movie Detail And Trend Explorer

**Goal:** Give each movie a useful home beyond its leaderboard row.

- Show poster, wins, losses, current Elo, rank, optional metadata, and comparison log.
- List every opponent, outcome, Elo delta, rank delta, and timestamp.
- Plot Elo over time for one or several selected movies.
- Use a shared chronological axis across selected movies.
- Compress only globally inactive intervals, with an explicit broken-time label such as
  "6 days with no votes"; never compress an interval containing any matchup event.
- Offer matchup count as an optional diagnostic graph axis.
- Let graph hover reveal opponent, outcome, Elo delta, rank delta, and timestamp.
- Show persistent rank movement over a chosen time or matchup range, not by session.

## Leaderboard And Library Management

### Leaderboard Finder And Filters

**Goal:** Make a large personal list easy to navigate.

- Search the leaderboard and jump directly to a movie.
- Filter by calibrated state, recently added status, rating range, or tags.
- Sort by win percentage, placement progress, date added, or recent activity.
- Do not offer rank and Elo as distinct sorts because they are the same ordering.
- Pin favorites and create custom watchlist tags.

### Per-Movie Administration

**Goal:** Safely correct or retire individual items without resetting the entire list.

- Reset one movie to 1000 Elo and 0 / 3 placement matches.
- Remove a movie with confirmation and an option to archive its matchup history.
- Add a poster-is-wrong flow that searches alternatives and lets the user choose the
  correct metadata result.
- Provide a data-health screen for missing posters, duplicate titles, invalid metadata,
  and movies still needing placement matches.

## Discovery And Bulk Add

### People Filmography Bulk Add

**Goal:** Add a director, actor, writer, studio, or similar person's work in one
controlled selection flow.

- Search for a person and load the complete paginated filmography, not only eight
  results.
- Filter by directing credits, feature films, release-year range, runtime, and
  exclusions such as shorts or documentaries.
- Present a poster grid with per-movie checkboxes, Select all, and Add selected.
- Review duplicates before committing and choose whether to skip, merge, or keep
  distinct versions.

### Franchise And Collection Builder

**Goal:** Add a coherent franchise while retaining control over exactly which movies
enter the ranking pool.

- Browse provider-backed movie collections where available.
- Support curated franchise builders for broader universes that are not one collection,
  including MCU phases, Star Wars eras, James Bond, and Studio Ghibli.
- Let the user select all, remove unwanted entries, and inspect duplicates before a
  batch add.

### Curated List And Attribute Bulk Add

**Goal:** Build lists from a wider set of discovery sources.

- Bulk add by decade, genre, country, production company, awards list, or a saved
  provider list.
- Import watchlists and ratings from Letterboxd, IMDb, Trakt, or a plain CSV.

## Arena Interaction And Visual Design

### Fast, Accessible Arena Controls

**Goal:** Keep repeated voting immediate and comfortable.

- Add keyboard controls for left, right, skip, back, and tie.
- Support fullscreen comparison with larger posters.
- Offer an optional hide-ratings mode to reduce anchoring bias.
- Show optional year, director, runtime, genre, and short synopsis under posters.
- Use a matchup queue only when it does not reveal choices too early.
- Improve poster-loading states.
- Complete an accessibility pass for high contrast, scalable text, keyboard navigation,
  and screen-reader labels.

### Non-Blocking Result Feedback

**Goal:** Make each vote feel satisfying while the next choice remains instant.

- Show a compact side panel for the previous result while the next matchup is already
  ready to click.
- Animate only changed Elo and rank with color, arrows, and a short count-up.
- Let rank movement slide or stay still as appropriate.
- Never impose an artificial delay, including a 500 ms animation gate.

### Modern Arena Redesign

**Goal:** Make the application feel polished rather than like a default desktop GUI.

- Establish a modern visual system, strong poster presentation, clearer hierarchy,
  faster transitions, and restrained light effects.
- Evaluate a web UI when the interaction, animation, and information-display needs
  outgrow CustomTkinter.
- Keep the real ranking experience first; visuals must not slow comparison flow.

## Ratings, Tiers, And Algorithm Releases

### Personal Rating Bands

**Goal:** Add expressive rank icons without pretending a personal movie list is a
universal competitive ladder.

- Keep exact ordinal rank and Elo separate from any badge or tier.
- Do not force a fixed percentage of movies into Bronze, Platinum, or Supersonic
  Legend.
- Permit a favorites-only list to have no low-tier movie or many high-tier movies.
- Use optional personal descriptive bands or configurable fixed thresholds, clearly
  labeled as personal rather than universal skill tiers.

### Global Competitive Tiers

**Goal:** Introduce Rocket League-style tiers only when a genuine shared pool can
support them.

- Reserve globally calibrated competitive tiers for a future shared pool with enough
  cross-user evidence, stable thresholds, and published methodology.
- Avoid dynamically forcing a desired tier distribution just to guarantee a certain
  number of top-tier movies.

### Ranking Algorithm Migration

**Goal:** Make ranking patches understandable and reversible.

- Version ranking rules and tier thresholds alongside matchup events.
- Support continuing with current Elo going forward for small changes.
- Support replaying saved matchup events under a new algorithm for coherent
  recalculation.
- Support a clearly labeled new season seeded from prior ratings rather than a flat
  reset to one number or crude checkpoints.

## Personal Data, Portability, And Profiles

### Local Profile System

**Goal:** Let multiple people use the same codebase or computer without mixing their
movie lists and rankings.

- Create a local profile on first startup with separate movies, leaderboard, matchup
  events, posters, and settings outside the code repository and ignored by Git.
- Seed new profiles from an optional default movie list, then let each diverge
  completely.
- Use an explicit profile chooser or local profile name, not computer fingerprinting.
- Later, link sign-in to a profile for backup and cross-device sync without accidental
  leaderboard mixing.

### Backup, Export, And Recovery

**Goal:** Make personal rankings safe to experiment with and easy to move.

- Create timestamped backups before resets, removals, and bulk operations.
- Import and export CSV or JSON backups, including ratings and matchup history.
- Add profile export/import for moving a private list between computers.
- Offer optional cloud backup or Git-based local data history.

### Portable And Web Distribution

**Goal:** Lower setup friction without abandoning local ownership.

- Package a portable Windows build so Python setup is unnecessary.
- Provide a local web version that can use the same local data.

## Shared And Global Rankings

### Global Preference Event Intake

**Goal:** Collect global evidence safely without confusing it with personal rankings.

- Keep personal leaderboards private and internally consistent.
- Make global ranking an opt-in aggregate, never a replacement for someone’s taste.
- Add authentication, rate limits, anti-bot controls, duplicate-account resistance,
  and repeat-vote rules before public rankings are trusted.
- Treat repeat choices of the same pair by one person as revisions or sharply decayed
  evidence, not unlimited additional wins and losses.

### Fair Global Contribution Weighting

**Goal:** Prevent a small, heavily replayed roster from dominating consensus.

- Aggregate pairwise preferences rather than raw global win/loss totals.
- Cap or decay each user-pair relationship.
- Normalize each person's total contribution so large and small rosters have fair
  influence.
- Consider more comparisons and a broader movie subset as useful evidence with
  diminishing returns, never unlimited weight.
- Do not merely reward broad portfolios with unlimited influence.

### Global Coverage And Confidence

**Goal:** Show how trustworthy a global position is, not just its score.

- Report distinct users, distinct opponent relationships, genre/franchise diversity,
  and uncertainty for every global movie.
- Down-weight narrow comparison islands for a general global ranking while preserving
  them as valid genre, franchise, or community signals.
- Detect bridge movies and users that connect otherwise separate taste clusters.
- Mark a movie with mostly superhero-only exposure as less globally certain than a
  movie tested across many audiences and opponent types.

### Multiple Shared Ranking Views

**Goal:** Avoid presenting one narrow consensus as universal taste.

- Support global, community, genre, franchise, and friend-group views.
- Separate broad consensus from niche preference.
- Use overlap between users' movie lists to connect preference communities and report
  uncertainty where cross-audience evidence is weak.

### Global Algorithm Versioning

**Goal:** Keep public rankings reproducible as the product improves.

- Store immutable preference events.
- Version every aggregate algorithm.
- Recompute derived global scores after ranking patches without discarding the original
  preferences.

## Metadata And Platform Foundations

### Metadata Provider Abstraction

**Goal:** Avoid structurally depending on one movie-data and poster provider.

- Treat TMDB as a development-time provider, not an assumed commercial asset source.
- Put metadata and poster retrieval behind a provider adapter.
- Define stable item records with local ID, external provider IDs, title, year, and
  media provenance.

### Commercial Metadata And Artwork Strategy

**Goal:** Prepare for a future public or commercial product responsibly.

- Review current TMDB terms plus image attribution and licensing before any public or
  commercial launch.
- Research licensed, open, public-domain, user-supplied, and paid artwork options.
- Avoid bulk scraping or mirroring a third-party poster catalog.
- Store only metadata and image rights the product is allowed to retain.

### Multi-Domain Ranking Foundation

**Goal:** Preserve a path beyond movies without forcing that complexity into the movie
experience now.

- Generalize around stable items and pairwise preferences so books, music, games, and
  other domains can reuse the engine later.

## Social And Fun

### Sharing And Recaps

**Goal:** Let a personal ranking be enjoyable to show without turning it into a social
network prematurely.

- Share a read-only ranking page or export a polished top-10 image.
- Create end-of-year recaps with most-compared films, biggest risers, and final top 10.

### Compare And Group Ranking

**Goal:** Explore taste with other people while retaining individual lists.

- Create separate rankings for different people, then compare their lists.
- Add group mode where several people vote and the app aggregates their preferences.

### Themes

**Goal:** Make the experience feel personal.

- Add theme packs based on genres, studios, or film eras.
