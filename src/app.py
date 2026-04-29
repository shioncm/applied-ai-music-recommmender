import os
import sys
import time

# app.py lives in src/ — add src/ itself to the path so sibling modules resolve
_SRC_DIR      = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
sys.path.insert(0, _SRC_DIR)

import streamlit as st
from dotenv import load_dotenv

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from recommender import load_songs, recommend_songs
from rag import parse_query, check_confidence, log_session

_CSV_PATH = os.path.join(_PROJECT_ROOT, "data", "songs.csv")
_LOG_PATH = os.path.join(_PROJECT_ROOT, "logs", "sessions.log")
_MODEL    = "gemini-2.5-flash-lite"

# ── Cached resources (created once per session) ───────────────────────────────

@st.cache_resource
def _get_client(api_key: str):
    from google import genai
    return genai.Client(api_key=api_key)


@st.cache_data
def _get_songs():
    return load_songs(_CSV_PATH)


# ── Streaming narrator (generator for st.write_stream) ────────────────────────

_NARRATOR_SYSTEM_PROMPT = """You are a warm, knowledgeable music recommendation assistant.
Your job is to explain why a set of retrieved songs match a user's request.

Rules you must follow:
- Mention EVERY song in the provided list by its exact title and artist name.
- Ground every claim in the score data provided — do not invent attributes.
- If a song only partially matches, say so honestly.
- Keep the tone conversational, like a friend who knows music well.
- Do not suggest songs that are not in the provided list."""


def _build_narrator_message(query: str, profile: dict, recommendations: list) -> str:
    acoustic_pref = "acoustic" if profile["likes_acoustic"] else "non-acoustic"
    lines = []
    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        lines.append(
            f"#{rank} \"{song['title']}\" by {song['artist']}  [score: {score:.2f} / 1.00]\n"
            f"   genre: {song['genre']} | mood: {song['mood']} | "
            f"energy: {song['energy']} | acousticness: {song['acousticness']}\n"
            f"   match breakdown: {reasons}"
        )
    songs_block = "\n\n".join(lines)
    return (
        f"The user asked: \"{query}\"\n\n"
        f"From their request I inferred these preferences:\n"
        f"  Genre:        {profile['favorite_genre']}\n"
        f"  Mood:         {profile['favorite_mood']}\n"
        f"  Energy level: {profile['target_energy']} / 1.0\n"
        f"  Acoustic:     {acoustic_pref}\n\n"
        f"Here are the top songs retrieved from the catalog:\n\n"
        f"{songs_block}\n\n"
        f"Explain to the user why each song fits (or partially fits) their request. "
        f"Reference every song by name and use the score data to justify your explanation."
    )


def _stream_narrative(client, query: str, profile: dict, recommendations: list):
    from google.genai import types
    stream = client.models.generate_content_stream(
        model=_MODEL,
        contents=_build_narrator_message(query, profile, recommendations),
        config=types.GenerateContentConfig(system_instruction=_NARRATOR_SYSTEM_PROMPT),
    )
    for chunk in stream:
        yield chunk.text or ""


# ── Page layout ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Song Seeker", page_icon="🎵", layout="centered")
st.title("🎵 Song Seeker")
st.caption("Describe what you want to hear and get personalized song recommendations.")

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    st.error("GEMINI_API_KEY is not set. Add it to your .env file.")
    st.stop()

client = _get_client(_api_key)
songs  = _get_songs()

query = st.text_input(
    "What kind of music are you in the mood for?",
    placeholder="e.g. something chill and acoustic for studying",
)

if st.button("Get Recommendations", type="primary", disabled=not query.strip()):

    # ── Step 1: parse query ──────────────────────────────────────────────────
    with st.spinner("Parsing your request..."):
        try:
            profile = parse_query(client, query)
        except RuntimeError as exc:
            st.error(str(exc))
            st.stop()

    st.subheader("Inferred Preferences")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Genre",       profile["favorite_genre"])
    c2.metric("Mood",        profile["favorite_mood"])
    c3.metric("Energy",      f"{profile['target_energy']:.2f}")
    c4.metric("Acoustic",    "Yes" if profile["likes_acoustic"] else "No")

    # ── Step 2: retrieve songs ───────────────────────────────────────────────
    recommendations = recommend_songs(profile, songs, k=5)

    # ── Step 3: confidence guardrail ─────────────────────────────────────────
    confident, warning = check_confidence(recommendations)

    if not confident:
        st.warning(warning)
        log_session(query, profile, recommendations,
                    confident=False, warning=warning, narrative="",
                    log_path=_LOG_PATH)
        st.stop()

    if warning:
        st.warning(warning)

    # ── Step 4: show retrieved songs ─────────────────────────────────────────
    st.subheader("Top Matches")
    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        with st.expander(f"#{rank}  **{song['title']}**  —  {song['artist']}  ·  score {score:.2f}"):
            cols = st.columns(4)
            cols[0].metric("Genre",        song["genre"])
            cols[1].metric("Mood",         song["mood"])
            cols[2].metric("Energy",       song["energy"])
            cols[3].metric("Acousticness", song["acousticness"])
            st.caption(f"Match breakdown: {reasons}")

    # ── Step 5: stream narrative ─────────────────────────────────────────────
    st.subheader("Why These Songs?")
    time.sleep(2)  # keep back-to-back requests inside rate limits
    try:
        narrative = st.write_stream(
            _stream_narrative(client, query, profile, recommendations)
        )
    except Exception as exc:
        st.error(f"Narrator error: {exc}")
        log_session(query, profile, recommendations,
                    confident=confident, warning=warning, narrative="",
                    log_path=_LOG_PATH)
        st.stop()

    # ── Step 6: log session ──────────────────────────────────────────────────
    log_session(query, profile, recommendations,
                confident=confident, warning=warning, narrative=narrative,
                log_path=_LOG_PATH)
    st.caption("Session logged → logs/sessions.log")
