"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from tabulate import tabulate

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Define three distinct user preference dictionaries
    high_energy_pop = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.85,
        "likes_acoustic": False,
        "target_tempo": 128.0,
        "target_valence": 0.86,
        "target_danceability": 0.82,
        "target_popularity": 90.0,
        "preferred_decade": "2020s",
        "preferred_mood_tags": "euphoric, uplifting",
    }

    chill_lofi = {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.38,
        "likes_acoustic": True,
        "target_tempo": 75.0,
        "target_valence": 0.58,
        "target_danceability": 0.55,
    }

    deep_intense_rock = {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.90,
        "likes_acoustic": False,
        "target_tempo": 150.0,
        "target_valence": 0.45,
        "target_danceability": 0.70,
    }

    # Use the first profile for recommendations.
    taste_profile = high_energy_pop
    scoring_modes = [
        ("genre-first", "Genre-First"),
        ("mood-first", "Mood-First"),
        ("energy-focused", "Energy-Focused"),
    ]

    for mode_key, mode_label in scoring_modes:
        recommendations = recommend_songs(taste_profile, songs, k=5, mode=mode_key)

        print("\n" + f"🎵 {mode_label} MUSIC RECOMMENDATIONS 🎵".center(70))

        rows = []
        for i, (song, score, explanation) in enumerate(recommendations, 1):
            reasons = "\n".join(f"- {reason.strip()}" for reason in explanation.split(";"))
            rows.append([i, song["title"], song["artist"], f"{song['genre']} / {song['mood']}", f"{score:.2f}", reasons])

        print(tabulate(
            rows,
            headers=["#", "Title", "Artist", "Genre / Mood", "Score", "Why It Was Recommended"],
            tablefmt="grid",
        ))
        print()


if __name__ == "__main__":
    main()
