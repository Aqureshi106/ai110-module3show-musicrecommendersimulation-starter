"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    taste_profile = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.82,
        "likes_acoustic": False,
        "target_tempo": 120.0,
        "target_valence": 0.84,
        "target_danceability": 0.79,
    }

    recommendations = recommend_songs(taste_profile, songs, k=5)

    print("\n" + "=" * 70)
    print("🎵 TOP MUSIC RECOMMENDATIONS FOR YOU 🎵".center(70))
    print("=" * 70)
    
    for i, rec in enumerate(recommendations, 1):
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        
        # Split reasons by semicolon for better formatting
        reasons = [reason.strip() for reason in explanation.split(";")]
        
        print(f"\n#{i} {song['title']}")
        print(f"    Artist: {song['artist']}")
        print(f"    Genre: {song['genre']} • Mood: {song['mood']}")
        print(f"    Match Score: {score:.2f}/10")
        print(f"    Why you'll love it:")
        for reason in reasons:
            print(f"      • {reason.capitalize()}")
        print("    " + "-" * 60)
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
