from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields converted to int/float."""
    import csv

    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["energy"] = float(row["energy"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            songs.append(row)

    print(f"Loaded songs: {len(songs)}")

    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a (score, reasons) tuple by applying the weighted genre/mood/energy/acoustic formula."""
    reasons = []

    # Genre match (weight: 0.35)
    if song["genre"] == user_prefs["favorite_genre"]:
        genre_contrib = 0.35
        reasons.append(f"genre match (+{genre_contrib:.2f})")
    else:
        genre_contrib = 0.0

    # Mood match (weight: 0.30)
    if song["mood"] == user_prefs["favorite_mood"]:
        mood_contrib = 0.30
        reasons.append(f"mood match (+{mood_contrib:.2f})")
    else:
        mood_contrib = 0.0

    # Energy similarity (weight: 0.20)
    energy_sim = 1.0 - abs(song["energy"] - user_prefs["target_energy"])
    energy_contrib = 0.20 * energy_sim
    reasons.append(f"energy similarity (+{energy_contrib:.2f})")

    # Acoustic match (weight: 0.15)
    acoustic_match = song["acousticness"] if user_prefs["likes_acoustic"] else 1.0 - song["acousticness"]
    acoustic_contrib = 0.15 * acoustic_match
    reasons.append(f"acoustic match (+{acoustic_contrib:.2f})")

    score = genre_contrib + mood_contrib + energy_contrib + acoustic_contrib
    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, then return the top-k results sorted highest to lowest."""
    # Score every song in the catalog using score_song as the judge
    scored = [
        (song, score, ", ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]

    # Sort into a new list ranked highest-to-lowest; original `songs` list is untouched
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    return ranked[:k]
