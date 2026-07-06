# AI Interactions Log

This file documents how an AI coding assistant (Claude) was used across the four challenge tasks: what was asked, what the AI changed, and how those changes were manually checked before being trusted. Line numbers refer to `src/recommender.py` and `src/main.py` as they exist in this repo.

---

## Challenge 1: Advanced Song Features

**Goal:** add 5+ complex attributes beyond the baseline (title, artist, genre, mood, energy, tempo, valence, danceability, acousticness) and wire them into scoring.

**Prompt used (paraphrased):**
> "Add popularity, release decade, and detailed mood tags to `data/songs.csv`, and update `recommender.py` so the scorer gives proximity/match points for them, with an explanation string per song like the existing reasons."

**What the AI generated:**
- 5 new columns added to `data/songs.csv`: `popularity` (0–100), `release_year`, `release_decade` (e.g. `"2020s"`), `mood_tags` (comma-separated, e.g. `"euphoric, radiant, uplifting"`), and `era_descriptor` (e.g. `"retro"`, `"modern"`, `"current"`).
- New helper functions in `src/recommender.py`:
  - `_split_tokens()` (line 72) — normalizes comma/pipe/semicolon-separated tag strings into a deduped, lowercased list.
  - `_parse_decade()` / `_decade_label()` (lines 92–118) — turns `"2020s"`, `"90s"`, or a 4-digit year into a comparable decade start integer.
  - `_decade_alignment_score()` (line 121) — full points if the song's decade matches the user's `preferred_decade`, partial credit one or two decades away, zero beyond that.
  - `_era_descriptor_target()` (line 144) — infers an era word (`"retro"`, `"throwback"`, `"modern"`, `"current"`) from the user's preferred decade or mood tags like `"nostalgic"`, and awards a bonus when the song's own `era_descriptor` matches.
  - `_mood_tempo_target()` / `_mood_valence_target()` / `_mood_decade_target()` (lines 34–69) — default numeric targets per mood label, so a user who only specifies `mood="happy"` still gets sensible tempo/valence/decade targets without typing them out.
  - Popularity proximity scoring added alongside the existing tempo/valence/danceability proximity terms in `_score_song_dict` (around line 304).
- `load_songs()` (line 479) updated to read and default all five new CSV columns.
- Each new feature appends a plain-language reason string (e.g. `"has popularity near your target (94/100) (+0.2)"`, `"fits your preferred era (2020s) (+1.4)"`, `"shares mood tags like euphoric, uplifting (+1.2)"`) so the "why" column in the terminal table stays accurate.

**Manual verification notes:**
- Ran `pytest` after the change — all 4 tests in `tests/test_recommender.py` still passed, confirming the new columns didn't break the existing `Song`/`UserProfile`/`Recommender` dataclass contract.
- Ran `python -m src.main` and manually checked a handful of reason strings against the raw CSV values by hand (e.g. confirmed "Sunrise City" really is `release_decade=2020s` and its `mood_tags` really do include `"uplifting"`) to make sure the new scoring terms weren't just plausible-looking but actually reading the right columns.
- Deliberately tested a song with an empty `mood_tags` field and a user profile with no `preferred_mood_tags` to confirm `_split_tokens()` returns `[]` instead of crashing on `None`.

---

## Challenge 2: Multiple Scoring Modes

**Goal:** let a user pick between at least two ranking strategies (e.g. genre-first vs. mood-first vs. energy-focused) without duplicating the whole scoring function.

**Prompt used (paraphrased):**
> "I want `main.py` to be able to run the same profile through 'genre-first,' 'mood-first,' and 'energy-focused' ranking strategies. Look at `recommender.py` and suggest a design pattern that avoids copy-pasting the scoring function four times."

**Design pattern brainstorm (AI + my review):** The AI suggested a **Strategy pattern**, but pointed out two ways to implement it in Python:
1. **Full Strategy pattern** — a `ScoringStrategy` interface/base class with one subclass per mode (`GenreFirstStrategy`, `MoodFirstStrategy`, ...), each overriding a `score()` method.
2. **Weight-table variant (chosen)** — keep one scoring function, and let "the strategy" be a small dictionary of feature weights that the function multiplies against. Switching modes just means looking up a different `Dict[str, float]`.

We went with option 2 (`_mode_weights()`, `src/recommender.py:165`), because the actual difference between modes here isn't the scoring *algorithm* — it's the same weighted-sum formula for all of them — the difference is only *how much* each feature counts. A full class hierarchy would add four subclasses that all override the same method with the same formula and different constants, which is more ceremony than the problem needs. The dictionary lookup keeps `_score_song_dict()` as a single source of truth for the scoring formula, while `mode` acts as the "which strategy" selector — the same value flows through `score_song()`, `recommend_songs()`, and `Recommender.recommend()`/`explain_recommendation()`, so both the functional API and the OOP `Recommender` class support all four modes without duplicating logic.

**What the AI generated:**
- `_mode_weights(mode)` (line 165): a `normalized_mode` lookup with four presets — `balanced` (all weights `1.0`), `genre-first` (genre weight `2.6`, everything else lowered), `mood-first` (mood weight `2.6`, mood-adjacent features like `tags`/`valence` bumped slightly), and `energy-focused` (energy weight `2.8`). Falls back to `balanced` for an unrecognized mode string instead of raising an error.
- `_score_song_dict(..., mode="balanced")` multiplies every scoring term by its matching weight from `_mode_weights(mode)`.
- `main.py` (line 56) loops over a `scoring_modes` list of `(mode_key, mode_label)` pairs and calls `recommend_songs(taste_profile, songs, k=5, mode=mode_key)` once per mode, printing a separate labeled table for each.

**Manual verification notes:**
- Ran the same `high_energy_pop` profile through all three modes printed by `main.py` and confirmed the rankings actually differ mode-to-mode (e.g. genre-first pulls pop/indie-pop songs higher; energy-focused pulls the highest-raw-energy songs higher even off-genre) — a strategy switch that produced identical output for every mode would mean the weights weren't actually wired in.
- Checked that an invalid/typo'd mode string (e.g. `"genre_first"` with an underscore) falls back to `balanced` instead of crashing, since `_mode_weights` uses `.get(normalized_mode, presets["balanced"])`.

---

## Challenge 3: Diversity and Fairness Logic

**Goal:** prevent one artist (or one genre) from crowding out the top-K list when their catalog entries all score similarly well.

**Rule implemented:** a **diversity penalty** — after sorting all songs by raw score, fill the K result slots one at a time. For each remaining slot, compute an *effective score* for every unpicked song as:

```
effective_score = raw_score - ARTIST_REPEAT_PENALTY * (number of already-picked songs by this song's artist)
```

with `ARTIST_REPEAT_PENALTY = 1.5` (`src/recommender.py:340`). Pick whichever song has the highest effective score, add it to the results, and increment that artist's pick count — so a second song by an artist who already has one pick starts 1.5 points in the hole, a third song by the same artist starts 3.0 points in the hole, and so on.

**Prompt used (paraphrased):**
> "Two songs by the same artist (Neon Echo) both keep scoring highly enough to take two of five slots in some profiles. Describe and implement a rule that penalizes a song's score when its artist already has a pick in the top results, without just hard-banning duplicate artists."

**What the AI generated:**
- `_select_diverse_top_k()` (`src/recommender.py:343`) — the greedy re-ranking loop described above. It's generic over "item" and takes a `get_artist` accessor function, so the same helper works for both the dict-based `recommend_songs()` (line 528) and the dataclass-based `Recommender.recommend()` (line 438) without duplicating the loop.
- A *penalty*, not a hard filter: an artist with a large enough score lead can still place two songs (e.g. if the gap is bigger than 1.5 points), which was an intentional design choice over an absolute "max 1 song per artist" rule — the model card documents this as a real limitation, not a guarantee.

**Manual verification notes:**
- Constructed the exact case called out in `README.md` — a `pop`/`happy` profile where Neon Echo's two songs ("Sunrise City", "Night Drive Loop") both land in the raw top 6 — and confirmed by hand that the second Neon Echo song drops out of the diversified top 5 once the 1.5-point penalty is applied, replaced by the next highest-scoring song from a different artist.
- Confirmed via `pytest` that diversification doesn't change results when there are no repeat artists in a profile's raw top-K (i.e., the penalty function is a no-op when it isn't needed, not an unconditional reshuffle).
- Note: this rule only penalizes repeat **artists**, not repeat **genres/moods** — I verified this by checking a profile whose raw top 5 was all "pop," which stayed all "pop" after diversification, since each song had a different artist. This gap is called out explicitly in `model_card.md` under Observed Behavior/Biases.

---

## Challenge 4: Visual Summary Table

**Goal:** make terminal output readable, with a formatted table that includes each song's title, artist, genre/mood, score, and — critically — the reasons behind its score.

**Prompt used (paraphrased):**
> "Suggest a way to print the recommendations as a table instead of a raw list, and make sure the 'why' reasons are visible per song, not just the score."

**What the AI generated (suggestion + implementation):**
- Suggested the `tabulate` library (already in `requirements.txt`) over hand-rolled ASCII formatting, since it handles column width, multi-line cells, and grid borders automatically — hand-rolled formatting would need to be redone every time a reason string got longer.
- `src/main.py` (lines 12, 67–76): builds one row per recommended song — `[#, title, artist, "genre / mood", score, reasons]` — where the `reasons` cell joins the semicolon-separated explanation string from `recommend_songs()` into one bullet per line (`"\n".join(f"- {r.strip()}" for r in explanation.split(";"))`), then calls `tabulate(rows, headers=[...], tablefmt="grid")`. `tabulate` renders each multi-line reasons cell inside its own bordered row.

**Manual verification notes:**
- Ran `python -m src.main` and visually confirmed the "Why It Was Recommended" column actually lists distinct, correctly-attributed reasons per song (spot-checked against the raw score contributions printed by a debug script) rather than a generic placeholder string.
- Confirmed the table still renders correctly for a song with only one contributing reason (the `if not reasons: reasons.append("fits the overall vibe profile")` fallback at `src/recommender.py:335`), so an all-zero-match song doesn't produce an empty or broken table cell.

---

## Overall Note on AI-Assisted Verification

Across all four challenges, the pattern I followed was: let the AI propose the change and draft code, then re-run the actual program (`pytest`, `python -m src.main`, and one-off scripts) myself and check specific printed numbers/reasons against the raw CSV and the scoring formulas by hand, rather than trusting the AI's description of what the code *should* do. This mattered in practice — see `README.md`'s adversarial-profile testing, which caught real behavior (e.g. `energy` not being range-clamped) that wasn't obvious from reading the code casually.
