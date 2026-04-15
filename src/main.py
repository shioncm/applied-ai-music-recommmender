"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Starter example profile: pop/happy listener who prefers non-acoustic tracks
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    width = 60
    genre  = user_prefs["favorite_genre"]
    mood   = user_prefs["favorite_mood"]
    header = f"  Top 5 Recommendations  |  {genre} / {mood}  "

    print("\n" + "=" * width)
    print(header.center(width))
    print("=" * width)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n #{rank}  {song['title']}  —  {song['artist']}")
        print(f"      Score : {score:.2f}")
        print(f"      Reasons:")
        for reason in explanation.split(", "):
            print(f"        • {reason}")

    print("\n" + "=" * width + "\n")


if __name__ == "__main__":
    main()
