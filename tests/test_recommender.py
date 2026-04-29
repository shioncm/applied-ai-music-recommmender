import os
import pytest
from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs, load_songs

_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ── Shared song fixtures for functional tests ────────────────────────────────

_POP_SONG  = {"id": 1, "title": "Happy Pop",   "artist": "A", "genre": "pop",  "mood": "happy",   "energy": 0.8, "tempo_bpm": 120, "valence": 0.9, "danceability": 0.8, "acousticness": 0.2}
_LOFI_SONG = {"id": 2, "title": "Chill Lofi",  "artist": "B", "genre": "lofi", "mood": "chill",   "energy": 0.4, "tempo_bpm": 80,  "valence": 0.6, "danceability": 0.5, "acousticness": 0.9}
_ROCK_SONG = {"id": 3, "title": "Rock Banger",  "artist": "C", "genre": "rock", "mood": "intense", "energy": 0.9, "tempo_bpm": 140, "valence": 0.5, "danceability": 0.7, "acousticness": 0.1}
_ALL_SONGS = [_POP_SONG, _LOFI_SONG, _ROCK_SONG]

_POP_USER = {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.8, "likes_acoustic": False}


# ── score_song tests ──────────────────────────────────────────────────────────

def test_score_song_full_match():
    # genre(0.35) + mood(0.30) + energy(0.20 * 1.0) + acoustic(0.15 * 0.8) = 0.97
    score, reasons = score_song(_POP_USER, _POP_SONG)
    assert abs(score - 0.97) < 0.01

def test_score_song_no_genre_or_mood_match():
    user = {"favorite_genre": "jazz", "favorite_mood": "sad", "target_energy": 0.5, "likes_acoustic": False}
    score, _ = score_song(user, _POP_SONG)
    # Only energy + acoustic contribute; score must be below 0.35 (genre weight)
    assert score < 0.35

def test_score_song_reasons_include_all_dimensions():
    _, reasons = score_song(_POP_USER, _POP_SONG)
    combined = " ".join(reasons)
    assert "genre" in combined
    assert "mood" in combined
    assert "energy" in combined
    assert "acoustic" in combined

def test_score_song_acoustic_preference():
    acoustic_user = {**_POP_USER, "likes_acoustic": True}
    score_acoustic, _ = score_song(acoustic_user, _LOFI_SONG)   # acousticness 0.9
    score_normal,   _ = score_song(_POP_USER,      _LOFI_SONG)   # acousticness 0.9, user wants non-acoustic
    # Acoustic user should score the lofi song higher on the acoustic dimension
    assert score_acoustic > score_normal


# ── recommend_songs tests ─────────────────────────────────────────────────────

def test_recommend_songs_top_result_is_best_match():
    results = recommend_songs(_POP_USER, _ALL_SONGS, k=3)
    assert results[0][0]["genre"] == "pop"
    assert results[0][0]["mood"] == "happy"

def test_recommend_songs_sorted_descending():
    results = recommend_songs(_POP_USER, _ALL_SONGS, k=3)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)

def test_recommend_songs_respects_k():
    results = recommend_songs(_POP_USER, _ALL_SONGS, k=2)
    assert len(results) == 2

def test_recommend_songs_k_larger_than_catalog():
    results = recommend_songs(_POP_USER, _ALL_SONGS, k=100)
    assert len(results) == len(_ALL_SONGS)

def test_recommend_songs_tuple_structure():
    results = recommend_songs(_POP_USER, _ALL_SONGS, k=1)
    song, score, reasons = results[0]
    assert isinstance(song, dict)
    assert isinstance(score, float)
    assert isinstance(reasons, str)


# ── load_songs tests (uses real songs.csv) ────────────────────────────────────

def test_load_songs_returns_nonempty_list():
    songs = load_songs(_CSV_PATH)
    assert isinstance(songs, list)
    assert len(songs) > 0

def test_load_songs_required_fields_present():
    songs = load_songs(_CSV_PATH)
    required = {"id", "title", "artist", "genre", "mood",
                "energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    for song in songs:
        assert required.issubset(song.keys())

def test_load_songs_numeric_fields_are_correct_types():
    songs = load_songs(_CSV_PATH)
    for song in songs:
        assert isinstance(song["id"],           int)
        assert isinstance(song["energy"],        float)
        assert isinstance(song["tempo_bpm"],     float)
        assert isinstance(song["valence"],       float)
        assert isinstance(song["danceability"],  float)
        assert isinstance(song["acousticness"],  float)

def test_load_songs_energy_in_valid_range():
    songs = load_songs(_CSV_PATH)
    for song in songs:
        assert 0.0 <= song["energy"] <= 1.0, f"energy out of range for {song['title']}"
        assert 0.0 <= song["acousticness"] <= 1.0
