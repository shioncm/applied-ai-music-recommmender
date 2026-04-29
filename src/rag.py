"""
RAG pipeline for the Music Recommender.

Components implemented here:
  - parse_query            : natural language → structured UserProfile dict
  - check_confidence       : guardrail that detects low-quality retrievals
  - narrate_recommendations: LLM narrator that cites retrieved songs
  - log_session            : writes each session to logs/sessions.log

All functions receive a google.genai.Client as their first argument so
the caller (main.py) controls client creation and the API key is never
hardcoded here.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from google import genai

# ── Catalog vocabulary ───────────────────────────────────────────────────────
# Kept here so the parser prompt always reflects the actual catalog.
# Update these lists if songs.csv gains new genres or moods.

CATALOG_GENRES = [
    "pop", "lofi", "rock", "metal", "jazz", "ambient", "synthwave",
    "indie pop", "r&b", "hip-hop", "electronic", "classical", "reggae",
    "blues", "country",
]

CATALOG_MOODS = [
    "happy", "chill", "intense", "relaxed", "focused", "moody",
    "romantic", "angry", "melancholic", "sad", "energetic", "peaceful",
    "euphoric", "uplifting",
]

# ── Pydantic schema for structured output ───────────────────────────────────

class _ParsedProfile(BaseModel):
    favorite_genre: str = Field(description="Closest genre from the catalog list")
    favorite_mood:  str = Field(description="Closest mood from the catalog list")
    target_energy:  float = Field(ge=0.0, le=1.0, description="Energy level 0.0–1.0")
    likes_acoustic: bool  = Field(description="True if the user prefers acoustic music")

# ── System prompt (defined once, reused across calls) ───────────────────────

_PARSER_SYSTEM_PROMPT = f"""You are a music preference parser.
Convert a natural-language music request into structured listening preferences.
Respond with a JSON object only — no explanation, no markdown fences.

You MUST always include all four fields:
  "favorite_genre"  : string  — closest genre from the list below.
  "favorite_mood"   : string  — closest mood from the list below.
  "target_energy"   : float   — 0.0 (very calm) to 1.0 (extremely energetic).
  "likes_acoustic"  : boolean — true if the user wants acoustic / unplugged music.

Available genres : {', '.join(CATALOG_GENRES)}
Available moods  : {', '.join(CATALOG_MOODS)}

Example output:
{{"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.8, "likes_acoustic": false}}

When in doubt, choose the most specific match rather than a generic one."""


# ── Query Parser ─────────────────────────────────────────────────────────────

def parse_query(client: "genai.Client", query: str) -> dict:
    """Convert a natural-language query into a UserProfile-compatible dict.

    Makes one structured-output call to gemini-2.5-flash-lite and returns a dict
    with keys: favorite_genre, favorite_mood, target_energy, likes_acoustic.

    Args:
        client: An initialised google.genai.Client.
        query:  Raw natural-language string from the user.

    Returns:
        dict with keys matching the UserProfile fields used by recommend_songs().

    Raises:
        RuntimeError: if the API call fails or returns an empty response.
    """
    from google.genai import types

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=_PARSER_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=_ParsedProfile,
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"[parse_query] API call failed: {exc}") from exc

    content = response.text
    if not content:
        raise RuntimeError("[parse_query] API returned an empty response.")

    try:
        data   = json.loads(content)
        parsed = _ParsedProfile(**data)
    except Exception as exc:
        raise RuntimeError(f"[parse_query] Failed to parse JSON response: {exc}") from exc

    return parsed.model_dump()


# ── Confidence Guardrail ──────────────────────────────────────────────────────

# Thresholds chosen from the project's stress-test observations:
#   - ghost-genre profiles top out at ~0.65 (genre weight is dead)
#   - conflicting profiles top out at ~0.70
#   - scores below 0.30 mean even energy + acoustic didn't align well
LOW_CONFIDENCE_THRESHOLD  = 0.30   # below this → no useful match at all
WEAK_CONFIDENCE_THRESHOLD = 0.50   # below this → match exists but is partial


def check_confidence(recommendations: list) -> tuple[bool, str]:
    """Evaluate whether the top retrieval results are strong enough to narrate.

    Inspects the scores returned by recommend_songs() and returns a
    (confident, message) tuple.  The caller should skip the narrator and
    show the message directly when confident is False.

    Args:
        recommendations: output of recommend_songs() —
                         List of (song_dict, score, reasons_str) tuples.

    Returns:
        (True,  "")          if the top result is a reasonable match.
        (False, warning_msg) if the top result is too weak to narrate.
    """
    if not recommendations:
        return False, (
            "No songs found in the catalog. "
            "Make sure data/songs.csv is loaded correctly."
        )

    top_score = recommendations[0][1]

    if top_score < LOW_CONFIDENCE_THRESHOLD:
        return False, (
            f"No strong matches found for your query "
            f"(best score: {top_score:.2f} / 1.00). "
            "Try rephrasing — for example, mention a genre or a mood."
        )

    if top_score < WEAK_CONFIDENCE_THRESHOLD:
        # Confident enough to continue, but the narrator should know
        return True, (
            f"Note: the best match scores only {top_score:.2f} / 1.00 — "
            "the catalog may not have a strong fit for this request."
        )

    return True, ""


# ── Narrator / Generator ──────────────────────────────────────────────────────

_NARRATOR_SYSTEM_PROMPT = """You are a warm, knowledgeable music recommendation assistant.
Your job is to explain why a set of retrieved songs match a user's request.

Rules you must follow:
- Mention EVERY song in the provided list by its exact title and artist name.
- Ground every claim in the score data provided — do not invent attributes.
- If a song only partially matches, say so honestly.
- Keep the tone conversational, like a friend who knows music well.
- Do not suggest songs that are not in the provided list."""


def _format_songs_for_prompt(recommendations: list) -> str:
    """Format retrieved songs as a readable block for the narrator prompt."""
    lines = []
    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        lines.append(
            f"#{rank} \"{song['title']}\" by {song['artist']}  [score: {score:.2f} / 1.00]\n"
            f"   genre: {song['genre']} | mood: {song['mood']} | "
            f"energy: {song['energy']} | acousticness: {song['acousticness']}\n"
            f"   match breakdown: {reasons}"
        )
    return "\n\n".join(lines)


def narrate_recommendations(
    client: "genai.Client",
    query: str,
    profile: dict,
    recommendations: list,
) -> str:
    """Stream a narrative that cites each retrieved song and explains its fit.

    This is the generation step of the RAG pipeline.  The retrieved songs are
    injected directly into the prompt — the LLM cannot answer without them.

    Args:
        client:          An initialised google.genai.Client.
        query:           The original natural-language query from the user.
        profile:         The parsed UserProfile dict returned by parse_query().
        recommendations: Top-k output from recommend_songs() —
                         List of (song_dict, score, reasons_str) tuples.

    Returns:
        The full narrative as a string (streamed to stdout while generating).

    Raises:
        RuntimeError: if the API call fails.
    """
    acoustic_pref = "acoustic" if profile["likes_acoustic"] else "non-acoustic"
    songs_block   = _format_songs_for_prompt(recommendations)

    user_message = (
        f"The user asked: \"{query}\"\n\n"
        f"From their request I inferred these preferences:\n"
        f"  Genre:             {profile['favorite_genre']}\n"
        f"  Mood:              {profile['favorite_mood']}\n"
        f"  Energy level:      {profile['target_energy']} / 1.0\n"
        f"  Acoustic:          {acoustic_pref}\n\n"
        f"Here are the top songs retrieved from the catalog:\n\n"
        f"{songs_block}\n\n"
        f"Explain to the user why each song fits (or partially fits) their request. "
        f"Reference every song by name and use the score data to justify your explanation."
    )

    from google.genai import types

    chunks: list[str] = []
    try:
        stream = client.models.generate_content_stream(
            model="gemini-2.5-flash-lite",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=_NARRATOR_SYSTEM_PROMPT,
            ),
        )
        for chunk in stream:
            text = chunk.text or ""
            print(text, end="", flush=True)
            chunks.append(text)
    except Exception as exc:
        raise RuntimeError(
            f"[narrate_recommendations] API call failed: {exc}"
        ) from exc

    print()  # newline after the stream ends
    return "".join(chunks)


# ── Session Logger ────────────────────────────────────────────────────────────

LOG_PATH = "logs/sessions.log"
_DIVIDER  = "=" * 72


def log_session(
    query: str,
    profile: dict,
    recommendations: list,
    confident: bool,
    warning: str,
    narrative: str,
    log_path: str = LOG_PATH,
) -> None:
    """Append a full session record to the log file.

    Creates the log directory automatically if it does not exist.
    Each record captures the complete RAG chain — query, inferred profile,
    retrieved songs, confidence result, and the generated narrative — so
    any session can be audited after the fact.

    Args:
        query:           The original natural-language query.
        profile:         Parsed UserProfile dict from parse_query().
        recommendations: Top-k output from recommend_songs().
        confident:       Whether check_confidence() passed.
        warning:         Warning string from check_confidence() (may be empty).
        narrative:       Full narrative string from narrate_recommendations()
                         (empty string if the session was blocked by the guardrail).
        log_path:        Path to the log file (default: logs/sessions.log).
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    acoustic_str = "acoustic" if profile.get("likes_acoustic") else "non-acoustic"

    confidence_line = (
        f"PASS  (top score: {recommendations[0][1]:.2f})"
        if confident and recommendations
        else f"FAIL  {warning}"
    )

    retrieved_lines = "\n".join(
        f"  #{rank}  \"{song['title']}\" by {song['artist']}  "
        f"[score: {score:.2f}]  genre: {song['genre']} | mood: {song['mood']}"
        for rank, (song, score, _) in enumerate(recommendations, start=1)
    )

    warning_block = f"\nWARNING   : {warning}" if warning and confident else ""

    narrative_block = (
        "\n".join(f"  {line}" for line in narrative.splitlines())
        if narrative
        else "  (blocked by confidence guardrail — no narrative generated)"
    )

    record = (
        f"\n{_DIVIDER}\n"
        f"TIMESTAMP : {timestamp}\n"
        f"QUERY     : {query}\n"
        f"PROFILE   : genre={profile.get('favorite_genre')} | "
        f"mood={profile.get('favorite_mood')} | "
        f"energy={profile.get('target_energy')} | "
        f"{acoustic_str}\n"
        f"CONFIDENCE: {confidence_line}"
        f"{warning_block}\n"
        f"RETRIEVED :\n{retrieved_lines}\n"
        f"NARRATIVE :\n{narrative_block}\n"
        f"{_DIVIDER}\n"
    )

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(record)
