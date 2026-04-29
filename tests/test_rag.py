import os
import tempfile

from src.rag import check_confidence, log_session

# ── Shared fixtures ───────────────────────────────────────────────────────────

_PROFILE = {
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.8,
    "likes_acoustic": False,
}

def _make_recs(top_score: float) -> list:
    song = {"title": "Song A", "artist": "Artist A", "genre": "pop",
            "mood": "happy", "energy": 0.8, "acousticness": 0.2}
    return [(song, top_score, "genre match (+0.35), mood match (+0.30)")]


# ── check_confidence tests ────────────────────────────────────────────────────

def test_check_confidence_empty_list():
    confident, msg = check_confidence([])
    assert confident is False
    assert "No songs" in msg

def test_check_confidence_below_low_threshold():
    confident, msg = check_confidence(_make_recs(0.20))
    assert confident is False
    assert "No strong matches" in msg

def test_check_confidence_weak_range_returns_true_with_warning():
    confident, msg = check_confidence(_make_recs(0.40))
    assert confident is True
    assert msg != ""                  # warning present
    assert "best match scores only" in msg

def test_check_confidence_strong_returns_true_no_warning():
    confident, msg = check_confidence(_make_recs(0.85))
    assert confident is True
    assert msg == ""

def test_check_confidence_at_low_boundary():
    # 0.30 is not *strictly less than* LOW_CONFIDENCE_THRESHOLD (0.30),
    # so it falls into the weak range and passes with a warning.
    confident, msg = check_confidence(_make_recs(0.30))
    assert confident is True
    assert msg != ""

def test_check_confidence_at_weak_boundary():
    # Score exactly at WEAK_CONFIDENCE_THRESHOLD (0.50) passes with no warning
    confident, msg = check_confidence(_make_recs(0.50))
    assert confident is True
    assert msg == ""


# ── log_session tests ─────────────────────────────────────────────────────────

def test_log_session_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        log_session("a happy song", _PROFILE, _make_recs(0.85),
                    confident=True, warning="", narrative="Great picks!",
                    log_path=log_path)
        assert os.path.exists(log_path)

def test_log_session_contains_query_and_narrative():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        log_session("a happy song", _PROFILE, _make_recs(0.85),
                    confident=True, warning="", narrative="Great picks!",
                    log_path=log_path)
        content = open(log_path).read()
        assert "a happy song" in content
        assert "Great picks!" in content

def test_log_session_records_retrieved_songs():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        log_session("a happy song", _PROFILE, _make_recs(0.85),
                    confident=True, warning="", narrative="Great picks!",
                    log_path=log_path)
        content = open(log_path).read()
        assert "Song A" in content
        assert "Artist A" in content

def test_log_session_shows_pass_when_confident():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        log_session("a happy song", _PROFILE, _make_recs(0.85),
                    confident=True, warning="", narrative="Great picks!",
                    log_path=log_path)
        assert "PASS" in open(log_path).read()

def test_log_session_shows_fail_when_not_confident():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        log_session("something weird", _PROFILE, _make_recs(0.20),
                    confident=False, warning="No strong matches found.",
                    narrative="", log_path=log_path)
        content = open(log_path).read()
        assert "FAIL" in content
        assert "No strong matches found." in content

def test_log_session_appends_multiple_records():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        log_session("query one", _PROFILE, _make_recs(0.85),
                    confident=True, warning="", narrative="First.",
                    log_path=log_path)
        log_session("query two", _PROFILE, _make_recs(0.85),
                    confident=True, warning="", narrative="Second.",
                    log_path=log_path)
        content = open(log_path).read()
        assert "query one" in content
        assert "query two" in content
