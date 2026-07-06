# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

BeatMatcher Mini 1.0

---

## 2. Intended Use

This model recommends 3 to 5 songs from a small, fixed catalog based on a user's stated preferences. It is designed for classroom learning about recommendation systems, not for production use.

Target users are students and instructors exploring how feature-based scoring works and how design choices can create bias.

---

## 3. How It Works (Short Explanation)

The recommender compares each song to a user profile and computes a total match score. The profile includes preferred genre, mood, energy target, acoustic preference, and optional numeric targets (tempo, valence, danceability).

Songs gain points for matching categorical preferences and for being numerically close to target values. In practice, energy similarity and acoustic preference can strongly influence ranking. After scoring all songs, the system sorts by score and returns the top results.

---

## 4. Data

The dataset in data/songs.csv contains 18 songs.

Each song includes:
- title and artist
- genre and mood labels
- energy, tempo_bpm, valence, danceability, acousticness

I did not add or remove songs from the provided catalog. The data covers several genres (for example pop, lofi, rock, jazz, electronic, metal, classical, hip hop), but representation is uneven. Some styles have only one song, so the catalog mostly reflects a narrow, synthetic sample rather than broad real-world listening diversity.

---

## 5. Strengths

- Transparent behavior: The scoring logic is easy to explain and debug.
- Strong performance on in-catalog preferences: Users with common profiles (for example pop + high energy or lofi + chill) receive results that feel intuitive.
- Good for experimentation: Weight changes and feature toggles quickly show how ranking behavior shifts.
- Fast and simple: No training step is required; scoring runs directly on metadata.

---

## 5b. Diversity / Fairness Component

The recommender fills its top-K list greedily: after sorting all songs by score, it picks one song at a time, and each time it subtracts an `ARTIST_REPEAT_PENALTY` of `1.5` points from any remaining song whose artist already has a pick in the result. This is a lightweight anti-filter-bubble measure — without it, an artist with several similarly-scoring songs (for example Neon Echo, which appears twice in the catalog) can occupy multiple slots in a 5-song list purely because their catalog entries are numerically close to the target profile, crowding out other reasonable matches.

This improves fairness in a narrow but concrete sense: it caps how much of a small, fixed result list one artist can dominate purely by having more catalog entries, so listeners see more variety and artists with only one strong song still get a fair shot at a slot. It is not a full fairness solution — a large enough score gap still lets one artist sweep the list, and the penalty does nothing for genre- or mood-level imbalance in the catalog (see Limitations below).

---

## 6. Limitations and Bias

- Small catalog limitation: Results are constrained by only 18 songs, which can cause weak matches for niche preferences.
- Representation bias: Underrepresented genres are disadvantaged because there are fewer candidates to recommend.
- Numeric-over-semantic bias: Songs with close numeric values can outrank songs that better match the user's stated genre or mood intent.
- Weight sensitivity: Minor weight changes can produce large ranking changes, making output stability fragile.
- Threshold artifacts: Acoustic preference uses hard cutoffs, so near-threshold songs can flip rank abruptly.
- Diversity risk: The same "central" songs can appear repeatedly across profiles, reducing recommendation variety. The artist-repeat penalty (Section 5b) reduces one form of this — a single artist sweeping the list — but does not address a "central song" appearing across many different users' lists, or genre/mood-level imbalance in the catalog.

If this were deployed in a real app, these effects could feel unfair to users whose taste is less represented in the catalog.

---

## 7. Evaluation

I evaluated the model with both normal and edge-case profiles and reviewed top-5 recommendations for each case.

Evaluation scenarios included:
- normal profiles (for example pop/happy/high-energy)
- conflicting profiles (for example lofi/sad with very high energy)
- empty or unknown categorical preferences
- impossible preference bundles
- mood-enabled vs mood-disabled comparisons
- changed scoring weights (original vs energy-heavy)

I also ran automated tests in tests/test_recommender.py. I did not use a formal numeric metric like precision@k; evaluation was qualitative, focused on whether outputs matched user intent and whether ranking changes were explainable.

---

## 8. Future Work

- Expand the catalog to improve genre and mood coverage.
- Rebalance weights so one strong numeric feature does not dominate semantic intent.
- Replace hard acoustic thresholds with smoother scoring.
- Add diversity-aware reranking so top results are less repetitive.
- Reintroduce and calibrate mood influence to better capture emotional intent.
- Add lightweight feedback loops so the system can adapt to a user's skips/likes over time.

---

## 9. Personal Reflection

This project made it clear that recommenders are not just about data; they are about choices in representation and weighting. Turning taste into numbers is powerful, but it can also flatten meaning. I was surprised by how often energy proximity overruled genre or mood expectations, especially in edge cases.

It also changed how I think about fairness in recommendation systems. Bias does not only come from harmful labels; it can come from coverage gaps, objective functions, and design defaults that repeatedly favor some tastes over others. Human judgment still matters for deciding whether recommendations feel appropriate, diverse, and respectful of user intent.