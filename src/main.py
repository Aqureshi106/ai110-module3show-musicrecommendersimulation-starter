"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse

from tabulate import tabulate

from .recommender import load_songs, recommend_songs

# Distinct user preference dictionaries a caller can pick between with --profile.
PROFILES = {
    "high-energy-pop": {
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
    },
    "chill-lofi": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.38,
        "likes_acoustic": True,
        "target_tempo": 75.0,
        "target_valence": 0.58,
        "target_danceability": 0.55,
    },
    "deep-intense-rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.90,
        "likes_acoustic": False,
        "target_tempo": 150.0,
        "target_valence": 0.45,
        "target_danceability": 0.70,
    },
}

# Scoring modes a caller can pick between with --mode; "all" (default) runs every mode in turn.
MODES = [
    ("balanced", "Balanced"),
    ("genre-first", "Genre-First"),
    ("mood-first", "Mood-First"),
    ("energy-focused", "Energy-Focused"),
]


def print_recommendations(taste_profile: dict, mode_key: str, mode_label: str, songs: list) -> None:
    """Print one tabulated recommendation table for a profile/mode combination."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Music Recommender Simulation from the command line.")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="high-energy-pop",
        help="Which user taste profile to score songs against (default: high-energy-pop).",
    )
    parser.add_argument(
        "--mode",
        choices=[key for key, _ in MODES] + ["all"],
        default="all",
        help="Which scoring strategy to use: balanced, genre-first, mood-first, energy-focused, "
             "or 'all' to run every mode back-to-back (default: all).",
    )
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    taste_profile = PROFILES[args.profile]

    modes_to_run = MODES if args.mode == "all" else [next(m for m in MODES if m[0] == args.mode)]
    for mode_key, mode_label in modes_to_run:
        print_recommendations(taste_profile, mode_key, mode_label, songs)


if __name__ == "__main__":
    main()
