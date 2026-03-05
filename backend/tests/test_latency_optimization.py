"""
Unit tests for StreamLatencyTracker and sentence boundary detection logic.

Tests cover:
- test_latency_tracker_basic: mark_start, mark_first_chunk, mark_end
- test_latency_tracker_per_stage: stt_start/end, llm_start, tts_start, first_audio
- test_voice_to_voice_metric: verify voice_to_voice_ms calculated correctly
- test_latency_tracker_reset: verify reset clears all state
- test_latency_tracker_no_start: verify empty metrics when start not called
- test_sentence_boundary_detection: test the sentence buffer logic
"""

import pytest
import time
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# StreamLatencyTracker tests
# ---------------------------------------------------------------------------

# We need to mock boto3 and settings to avoid real AWS connections when importing
# the module, since NovaSonicStreamSession.__init__ creates a bedrock client.
# However, StreamLatencyTracker is a standalone class that does not use boto3.
# We import it with patching to avoid side effects from module-level code.

@pytest.fixture
def tracker():
    """Create a fresh StreamLatencyTracker instance."""
    from app.services.nova_sonic_stream import StreamLatencyTracker
    return StreamLatencyTracker()


def test_latency_tracker_basic(tracker):
    """Basic latency tracking: start -> first_chunk -> end."""

    tracker.mark_start()
    # Simulate some processing time
    time.sleep(0.01)
    tracker.mark_first_chunk()
    time.sleep(0.01)
    tracker.mark_end()

    metrics = tracker.get_metrics()

    assert "time_to_first_chunk_ms" in metrics
    assert "total_latency_ms" in metrics

    # Both should be positive
    assert metrics["time_to_first_chunk_ms"] > 0
    assert metrics["total_latency_ms"] > 0

    # total_latency should be >= time_to_first_chunk
    assert metrics["total_latency_ms"] >= metrics["time_to_first_chunk_ms"]


def test_latency_tracker_per_stage(tracker):
    """Per-stage latency metrics: STT, LLM first token, TTS first audio."""

    tracker.mark_start()

    # STT stage
    tracker.mark_stt_start()
    time.sleep(0.01)
    tracker.mark_stt_end()

    # LLM stage
    tracker.mark_llm_start()
    time.sleep(0.01)
    tracker.mark_first_chunk()

    # TTS stage
    tracker.mark_tts_start()
    time.sleep(0.01)
    tracker.mark_first_audio()

    tracker.mark_end()

    metrics = tracker.get_metrics()

    assert "stt_ms" in metrics
    assert "llm_first_token_ms" in metrics
    assert "tts_first_audio_ms" in metrics
    assert "voice_to_voice_ms" in metrics
    assert "total_latency_ms" in metrics

    # All stage durations should be positive
    assert metrics["stt_ms"] > 0
    assert metrics["llm_first_token_ms"] > 0
    assert metrics["tts_first_audio_ms"] > 0


def test_voice_to_voice_metric(tracker):
    """voice_to_voice_ms should be the time from start to first_audio."""

    tracker.mark_start()
    # Simulate the full pipeline
    tracker.mark_stt_start()
    tracker.mark_stt_end()
    tracker.mark_llm_start()
    tracker.mark_first_chunk()
    tracker.mark_tts_start()
    time.sleep(0.05)  # Simulate TTS processing
    tracker.mark_first_audio()

    metrics = tracker.get_metrics()

    assert "voice_to_voice_ms" in metrics
    # voice_to_voice should be >= 50ms (we slept 50ms)
    assert metrics["voice_to_voice_ms"] >= 40  # Allow slight timing variance


def test_voice_to_voice_metric_precise(tracker):
    """voice_to_voice_ms should equal (first_audio - start) * 1000."""

    # Use direct attribute manipulation for a precise test
    tracker._start_time = 100.0  # seconds
    tracker._first_audio = 100.250  # 250ms later

    metrics = tracker.get_metrics()

    assert "voice_to_voice_ms" in metrics
    assert metrics["voice_to_voice_ms"] == 250.0


def test_latency_tracker_reset(tracker):
    """reset() should clear all tracked timestamps."""

    tracker.mark_start()
    tracker.mark_stt_start()
    tracker.mark_stt_end()
    tracker.mark_llm_start()
    tracker.mark_first_chunk()
    tracker.mark_tts_start()
    tracker.mark_first_audio()
    tracker.mark_end()

    # Before reset, should have metrics
    metrics_before = tracker.get_metrics()
    assert len(metrics_before) > 0

    tracker.reset()

    # After reset, should have no metrics
    metrics_after = tracker.get_metrics()
    assert len(metrics_after) == 0


def test_latency_tracker_no_start(tracker):
    """Without calling mark_start, get_metrics should return empty dict."""

    tracker.mark_first_chunk()
    tracker.mark_end()

    metrics = tracker.get_metrics()
    assert metrics == {}


def test_first_chunk_only_set_once(tracker):
    """mark_first_chunk should only record the first call, ignoring subsequent ones."""

    tracker.mark_start()
    time.sleep(0.01)
    tracker.mark_first_chunk()

    first_metrics = tracker.get_metrics()
    first_time = first_metrics["time_to_first_chunk_ms"]

    # Call mark_first_chunk again after more time
    time.sleep(0.02)
    tracker.mark_first_chunk()

    second_metrics = tracker.get_metrics()
    second_time = second_metrics["time_to_first_chunk_ms"]

    # Should be the same value, not updated
    assert first_time == second_time


def test_first_audio_only_set_once(tracker):
    """mark_first_audio should only record the first call, ignoring subsequent ones."""

    tracker.mark_start()
    tracker.mark_tts_start()
    time.sleep(0.01)
    tracker.mark_first_audio()

    metrics1 = tracker.get_metrics()
    v2v_1 = metrics1["voice_to_voice_ms"]

    time.sleep(0.02)
    tracker.mark_first_audio()

    metrics2 = tracker.get_metrics()
    v2v_2 = metrics2["voice_to_voice_ms"]

    # Should be the same value
    assert v2v_1 == v2v_2


# ---------------------------------------------------------------------------
# Sentence boundary detection tests
# ---------------------------------------------------------------------------
# The sentence boundary detection logic lives inline in the streaming loop
# of NovaSonicStreamSession._stream_model_response. We test the algorithm
# as a standalone function to verify correctness without needing a live session.

def _detect_sentence_boundaries(buffer, punctuation_marks=None):
    """
    Replicate the sentence boundary detection algorithm from nova_sonic_stream.py.

    This is the same logic used in the streaming response handler to split
    accumulated text into speakable sentences at punctuation boundaries.

    Returns (sentences_found, remaining_buffer).
    """
    if punctuation_marks is None:
        punctuation_marks = ['. ', '! ', '? ', '.\n', '!\n', '?\n']

    sentences = []
    while buffer:
        boundary = -1
        for punct in punctuation_marks:
            idx = buffer.find(punct)
            if idx != -1 and (boundary == -1 or idx < boundary):
                boundary = idx + len(punct)
        if boundary == -1:
            break
        sentence = buffer[:boundary].strip()
        buffer = buffer[boundary:]
        if sentence:
            sentences.append(sentence)

    return sentences, buffer


def test_sentence_boundary_single_sentence():
    """A single complete sentence ending with '. ' should be detected."""

    sentences, remaining = _detect_sentence_boundaries(
        "Hello, welcome to our clinic. "
    )

    assert len(sentences) == 1
    assert sentences[0] == "Hello, welcome to our clinic."
    assert remaining == ""


def test_sentence_boundary_multiple_sentences():
    """Multiple sentences should all be split correctly."""

    text = "Hello there. How can I help you? I can book an appointment! "
    sentences, remaining = _detect_sentence_boundaries(text)

    assert len(sentences) == 3
    assert sentences[0] == "Hello there."
    assert sentences[1] == "How can I help you?"
    assert sentences[2] == "I can book an appointment!"


def test_sentence_boundary_incomplete_sentence():
    """An incomplete sentence (no trailing punctuation+space) should remain in the buffer."""

    text = "Hello there. I am currently checking"
    sentences, remaining = _detect_sentence_boundaries(text)

    assert len(sentences) == 1
    assert sentences[0] == "Hello there."
    assert remaining == "I am currently checking"


def test_sentence_boundary_no_boundary():
    """Text with no sentence-ending punctuation should stay entirely in the buffer."""

    text = "still thinking about the answer"
    sentences, remaining = _detect_sentence_boundaries(text)

    assert len(sentences) == 0
    assert remaining == "still thinking about the answer"


def test_sentence_boundary_newline_punctuation():
    """Sentence boundaries with newlines should be detected."""

    text = "First sentence.\nSecond sentence.\n"
    sentences, remaining = _detect_sentence_boundaries(text)

    assert len(sentences) == 2
    assert sentences[0] == "First sentence."
    assert sentences[1] == "Second sentence."


def test_sentence_boundary_incremental_accumulation():
    """Simulate incremental text accumulation as in the streaming response loop."""

    buffer = ""
    all_sentences = []

    # Simulate text chunks arriving from the LLM
    chunks = [
        "Hello, ",
        "welcome to ",
        "our clinic. ",
        "How can I ",
        "help you today? ",
        "We have openings",
        " this week.",
    ]

    for chunk in chunks:
        buffer += chunk
        sentences, buffer = _detect_sentence_boundaries(buffer)
        all_sentences.extend(sentences)

    # The last chunk "this week." has no trailing space, so it stays in the buffer
    assert len(all_sentences) == 2
    assert all_sentences[0] == "Hello, welcome to our clinic."
    assert all_sentences[1] == "How can I help you today?"
    assert "this week." in buffer


def test_sentence_boundary_exclamation_and_question():
    """Exclamation marks and question marks should both be valid boundaries."""

    text = "Great! What time works for you? Morning is available. "
    sentences, remaining = _detect_sentence_boundaries(text)

    assert len(sentences) == 3
    assert sentences[0] == "Great!"
    assert sentences[1] == "What time works for you?"
    assert sentences[2] == "Morning is available."
