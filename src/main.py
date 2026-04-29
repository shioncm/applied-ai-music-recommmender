"""
Command line runner for the Music Recommender Simulation.

Usage:
  python -m src.main            # batch mode: runs all preset profiles (original)
  python -m src.main --chat     # RAG chat mode: natural language queries via Gemini

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse
import os
import sys
import time

# When run as `python -m src.main`, the project root is on sys.path but not
# src/ itself. Insert src/ so sibling imports (recommender, rag) resolve.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from recommender import load_songs, recommend_songs

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CSV_PATH     = os.path.join(_PROJECT_ROOT, "data", "songs.csv")
_ENV_PATH     = os.path.join(_PROJECT_ROOT, ".env")

load_dotenv(_ENV_PATH)

from rag import (
    parse_query,
    check_confidence,
    narrate_recommendations,
    log_session,
)


PROFILES = [
    # ── Standard profiles ───────────────────────────────────────────
    {
        "name": "Default Pop / Happy",
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    },
    {
        "name": "High-Energy Pop",
        "favorite_genre": "pop",
        "favorite_mood": "intense",
        "target_energy": 0.93,
        "likes_acoustic": False,
    },
    {
        "name": "Chill Lofi",
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.40,
        "likes_acoustic": True,
    },
    {
        "name": "Deep Intense Rock",
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.91,
        "likes_acoustic": False,
    },
    # ── Adversarial / edge-case profiles ────────────────────────────
    {
        # Conflicting: sad mood but extreme high energy.
        # No song in the catalog is both sad AND high-energy, so every
        # result has to sacrifice either mood or energy — max possible
        # score is ~0.70.  Tests whether the scorer degrades gracefully
        # instead of silently promoting a wrong match.
        "name": "[EDGE] Sad Bangers",
        "favorite_genre": "blues",
        "favorite_mood": "sad",
        "target_energy": 0.95,
        "likes_acoustic": False,
    },
    {
        # Ghost genre: "k-pop" does not exist in the catalog, so
        # genre_contrib is always 0.0.  The top results win purely on
        # mood + energy + acoustic — genre match (worth 0.35) is dead
        # weight.  Maximum achievable score is 0.65.
        "name": "[EDGE] Ghost Genre (k-pop)",
        "favorite_genre": "k-pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    },
    {
        # Contradictory acoustic preference: the user wants electronic /
        # euphoric music (inherently non-acoustic) but also likes_acoustic.
        # The best genre+mood match (Bassline District, acousticness 0.03)
        # will be penalised on the acoustic dimension, while highly
        # acoustic songs score well acoustically but miss genre and mood.
        "name": "[EDGE] Acoustic Electronic",
        "favorite_genre": "electronic",
        "favorite_mood": "euphoric",
        "target_energy": 0.92,
        "likes_acoustic": True,
    },
]

_WIDTH = 62


def print_recommendations(profile: dict, recommendations: list) -> None:
    width = _WIDTH
    name = profile["name"]
    genre = profile["favorite_genre"]
    mood = profile["favorite_mood"]
    energy = profile["target_energy"]
    acoustic = "acoustic" if profile["likes_acoustic"] else "non-acoustic"

    print("\n" + "=" * width)
    print(f"  {name}".ljust(width))
    print(f"  {genre} / {mood} | energy {energy} | {acoustic}".ljust(width))
    print("=" * width)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score : {score:.2f}")
        print(f"       Reasons:")
        for reason in explanation.split(", "):
            print(f"         • {reason}")

    print()


def interactive_mode(songs: list) -> None:
    """RAG chat loop: parse a natural-language query, retrieve songs,
    run the confidence guardrail, stream a narrative, and log everything.
    """
    try:
        from google import genai
    except ImportError:
        print("Error: 'google-genai' package is not installed.")
        print("Run:  pip install google-genai")
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Add it to your .env file:  GEMINI_API_KEY=your-key-here")
        return

    client = genai.Client(api_key=api_key)

    print("\n" + "=" * _WIDTH)
    print("  Music Recommender — Chat Mode".ljust(_WIDTH))
    print("  Describe what you want to hear. Type 'quit' to exit.".ljust(_WIDTH))
    print("=" * _WIDTH)

    while True:
        print()
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat mode.")
            break

        if not query:
            continue
        if query.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        # ── Step 1: parse natural language → structured profile ──────
        print("\n  Parsing your request...")
        try:
            profile = parse_query(client, query)
        except RuntimeError as exc:
            print(f"\n  [Error] {exc}")
            continue

        acoustic_label = "Yes" if profile["likes_acoustic"] else "No"
        print(f"\n  Inferred preferences:")
        print(f"    Genre    : {profile['favorite_genre']}")
        print(f"    Mood     : {profile['favorite_mood']}")
        print(f"    Energy   : {profile['target_energy']}")
        print(f"    Acoustic : {acoustic_label}")

        # ── Step 2: retrieve top-5 songs using existing scorer ───────
        recommendations = recommend_songs(profile, songs, k=5)

        # ── Step 3: confidence guardrail ─────────────────────────────
        confident, warning = check_confidence(recommendations)

        if not confident:
            print(f"\n  ⚠  {warning}")
            log_session(
                query=query,
                profile=profile,
                recommendations=recommendations,
                confident=False,
                warning=warning,
                narrative="",
            )
            continue

        if warning:
            print(f"\n  ⚠  {warning}")

        time.sleep(2)  # avoid back-to-back requests hitting the burst limit

        # ── Step 4: stream narrative grounded in retrieved songs ──────
        print(f"\n  {'-' * (_WIDTH - 2)}")
        try:
            narrative = narrate_recommendations(client, query, profile, recommendations)
        except RuntimeError as exc:
            print(f"\n  [Error] {exc}")
            log_session(
                query=query,
                profile=profile,
                recommendations=recommendations,
                confident=confident,
                warning=warning,
                narrative="",
            )
            continue

        # ── Step 5: log the full session ─────────────────────────────
        log_session(
            query=query,
            profile=profile,
            recommendations=recommendations,
            confident=confident,
            warning=warning,
            narrative=narrative,
        )
        print(f"  Session logged → logs/sessions.log")
        print(f"  {'-' * (_WIDTH - 2)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Run in RAG chat mode (requires GEMINI_API_KEY)",
    )
    args = parser.parse_args()

    songs = load_songs(_CSV_PATH)

    if args.chat:
        interactive_mode(songs)
    else:
        for profile in PROFILES:
            recommendations = recommend_songs(profile, songs, k=5)
            print_recommendations(profile, recommendations)


if __name__ == "__main__":
    main()
