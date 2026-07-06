# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

BeatMatcher Mini 1.0

---

## 2. Goal / Task

This model picks 5 songs out of a small catalog that best match one listener's stated taste.

The listener tells it things like: favorite genre, favorite mood, how much energy they want, whether they like acoustic songs, and (optionally) a target tempo, mood, danceability, popularity, decade, or era. The model doesn't "understand" music. It just compares numbers and labels, gives points for close matches, adds up the points per song, and returns the 5 songs with the highest total.

---

## 3. Data Used

The dataset is `data/songs.csv`. It has 18 songs. I didn't add or remove any.

Each song has:
- a title and an artist
- a genre and a mood label (e.g. pop / happy, lofi / chill)
- five 0–1 style numbers: energy, valence, danceability, acousticness, plus tempo in BPM
- a popularity score, release year/decade, some mood tags, and an "era" word

18 songs is a tiny catalog. Some genres (metal, classical, jazz) only have one song each, so those listeners get thin, sometimes weak, matches no matter what the scoring logic does. The data itself limits what "good" recommendations can even look like.

---

## 4. Algorithm Summary (Plain Language)

For every song, the system asks a list of small questions and adds up points:

- Does the genre match what I asked for? If yes, add a point.
- Does the mood match? If yes, add a point.
- How close is the song's energy to my target energy? The closer, the more points (up to 6 — this is the single biggest score source).
- How close is the tempo, mood-positivity (valence), danceability, and popularity to what I asked for or what's typical for my mood? Closer = more points, each capped lower than energy.
- Does the song's era fit the decade I like? Do its mood tags overlap with mine? Small bonus points if so.
- Do I like acoustic songs, and does this song's acousticness match that? Up to 2 bonus points.

All the points get added into one score per song. Songs are then sorted highest score first (ties broken alphabetically by title). Before the final top-5 is picked, the system also runs a fairness step: if an artist already has a song in the list, their other songs lose 1.5 points each so one artist can't fill the whole list just because they happen to have several catalog entries close to the target.

There's no training, no learning, and no memory between runs — it's a fresh calculation every time, based only on the numbers you feed in.

---

## 4b. Diversity / Fairness Component

Before returning the final top-5, the system re-ranks with a fairness rule: for every artist who already has a song in the results, their *other* songs lose 1.5 points before the next slot is filled. So if an artist's first song is picked, their second song effectively needs to beat the next-best competitor by more than 1.5 points to also make the list.

**Why this helps:** without this rule, one artist who happens to have several songs that are all numerically close to a listener's target (for example Neon Echo, which has two songs in this catalog) can take 2 or more of the 5 slots purely because their catalog has more entries near the target — not because those songs are actually better matches than songs by other artists. The penalty gives artists with only one strong song a real shot at a slot, and it means a 5-song list reflects 5 different artists more often than not, which feels more like a varied playlist and less like a single artist's back catalog.

**Why it's not a full fix:** it only looks at the artist field. If one *genre* or *mood* dominates the catalog (there are far more pop songs than metal songs, for example), this rule does nothing about that — a top-5 list can still be all-pop even after the artist penalty is applied, as long as each pop song is by a different artist. It's also not an absolute cap: if one artist's song is a much better match (more than 1.5 points ahead), they can still take two slots. See Observed Behavior below for the genre/mood-level gap this leaves.

---

## 5. Observed Behavior / Biases

- **Energy dominates.** Because the energy match is worth up to 6 points and everything else is worth 1–2, songs with the right "feel" of intensity almost always rank ahead of songs that only match genre or mood. A song can miss the user's stated genre and mood entirely and still land in the top 5 purely because its energy number is close.
- **Contradictory requests get silently resolved in favor of energy.** If someone asks for `lofi` + `sad` but also sets `energy=0.9` (a combination that doesn't really exist in real music), the system doesn't flag the contradiction. It just drops lofi/sad from consideration and returns a high-energy song from a totally different genre.
- **A missing safety check on the energy number causes a bigger problem than expected.** The system never checks that energy is between 0 and 1. If someone accidentally sends `energy=5.0` (e.g., a UI slider bug, or a 0–10 scale mixed up with 0–1), every song's energy score quietly drops to zero — the biggest scoring factor just vanishes, and nobody is told. The list still looks like a normal top-5, but it was built on far less information than a normal run.
- **A yes/no setting can flip by accident.** The "do you like acoustic songs" preference is read as a plain true/false. If a caller accidentally passes the text `"false"` instead of the real value `False`, Python treats any non-empty piece of text as "true" — so the system thinks the listener *wants* acoustic songs, the opposite of what was meant. Nothing crashes; it just quietly does the wrong thing.
- **Unknown genres/moods fail invisibly.** If a listener's genre or mood isn't anywhere in the 18-song catalog (or has a typo), the system doesn't say "I don't have that" — it just scores every song as a non-match on that trait and moves on, so the result still looks confident even though it's really just falling back to energy and popularity.
- **Small catalog = repeat winners.** A handful of songs (like "Gym Hero" and "Sunrise City") are numerically close to a lot of different target profiles, so they show up across many different, unrelated user profiles. That's not because they're "the best" song for everyone — it's because the 18-song catalog doesn't have much variety, so a few songs end up sitting near the middle of almost every measurement.

---

## 6. Evaluation Process

I tested the system with normal profiles (e.g. pop + happy + high energy) and with a set of "adversarial" edge-case profiles built specifically to try to break or confuse the scoring logic:

1. A profile asking for `lofi` + `sad` but with `energy=0.9` (contradictory request)
2. A profile with `likes_acoustic="false"` passed as text instead of a real True/False value
3. A profile with `energy=5.0`, five times over the normal 0–1 scale
4. A profile asking for a genre and mood (`vaporwave`, `euphoric-sad`) that don't exist anywhere in the catalog

I ran each of these through the real code (not a mockup) and pasted the actual terminal output into `README.md` (see "Adversarial Profile Runs") so the results can be checked against the real program instead of taken on faith.

I also tried one weight-shift experiment: cutting the genre-match weight in half and doubling the energy weight, then re-running the same normal profile. The math stayed valid — nothing broke, no negative scores — but a hip-hop song that didn't match the listener's stated `pop` genre jumped ahead of a song that did, just because it had slightly better energy. That showed me the weights aren't just tuning knobs; changing them decides who gets served well and who doesn't.

I didn't use a formal accuracy metric (no precision@k, no ground truth labels) since there's no "correct answer" dataset here. Evaluation was judgment-based: does the output make sense for what the person asked for, and can I explain why each song ranked where it did?

---

## 7. Intended Use and Non-Intended Use

**Intended use:** classroom learning. This is meant to help students and instructors see, in a small and readable way, how turning taste into numbers and weights creates a ranked list — and how that process can go wrong. It's meant to be read, poked at, and broken on purpose.

**Not intended for:**
- Real music recommendations for real listeners. The catalog is 18 fake-ish songs; it has no idea what your actual music taste is.
- Any use where the ranking needs to be fair across many different listeners at scale — this system has no protection against the biases described above beyond the one narrow artist-repeat rule.
- Feeding it unchecked user input in a live product. As shown above, it doesn't validate numeric ranges or types, so bad input (wrong scale, wrong type) fails silently instead of raising an error.

---

## 8. Ideas for Improvement

- Validate and clamp inputs (especially `energy`) so an out-of-range number can't silently zero out the biggest scoring factor.
- Lower the energy weight relative to genre/mood, or at least warn the user when their stated genre/mood doesn't exist in the catalog, instead of quietly ignoring it.
- Smooth out the acoustic preference's hard on/off cutoff into a gradual score, so a song one point away from the threshold doesn't flip between "counts" and "doesn't count."

---

## 9. Personal Reflection

**Biggest learning moment:** Running the `energy=5.0` test and watching every single song's energy score print `+0.0` was the moment this stopped feeling like "just weights and numbers" and started feeling like a real bug report. I expected a strange or biased result. I didn't expect the model's single biggest scoring factor to just disappear without any error message, while the output still looked perfectly normal. That taught me that the scariest bugs in a scoring system aren't the ones that crash — they're the ones that keep producing a confident-looking answer while quietly running on broken input.

**Using AI tools, and when I had to double-check them:** I used Claude to help design the adversarial test profiles, run them against the actual `recommender.py` code, and draft this documentation. The part I had to double-check most carefully was making sure every number and ranking written in the README and this model card came from actually executing the code — not from the AI describing what it *expected* to happen. A few of my early experiment write-ups in the README (like the older "Pair 4" weight experiment) referenced formulas and point values that no longer match the current code, which is exactly the kind of thing that's easy for an AI (or a person) to leave stale after the code changes. I re-ran the real program for every number that ended up in this version instead of trusting a remembered or predicted result.

**What surprised me about simple algorithms "feeling" like recommendations:** Even though this system is just "add up some proximity scores and sort," the good results genuinely feel like real recommendations — pop/happy/high-energy listeners get pop songs that feel right. That surprised me. It made it clearer how something as simple as weighted addition can produce output a real person interprets as "the system gets me," even though there's no learning, no listening history, and no real understanding involved. It also means the *bad* results (like getting a cinematic song for a "sad lofi" request) feel just as confident and "recommendation-shaped" as the good ones, which is exactly what makes this kind of bias easy to miss unless you go looking for it.

**What I'd try next:** I'd want to fix the energy-clamping bug and the acoustic string/boolean bug first, since those are real correctness issues, not just design tradeoffs. After that, I'd try adding a simple "confidence" signal — something that tells the user when their genre/mood isn't in the catalog, or when a numeric input looks out of range — so the system can say "I'm guessing here" instead of always returning a polished-looking top 5.
