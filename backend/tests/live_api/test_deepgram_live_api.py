"""Opt-in Deepgram connection smoke test.

The test opens and closes a real Flux WebSocket but sends no audio, so it
checks credentials, model access, DNS/TLS, and the provider handshake without
submitting player speech.
"""

from __future__ import annotations

import os
import time

import pytest

from app.config import AppConfig
from app.services.transcription_service import (
    DeepgramSession,
    TranscriptionCallbacks,
)

pytestmark = pytest.mark.live_api

CONNECT_TIMEOUT_SECONDS = 15


def _require_live_api_opt_in() -> None:
    if os.getenv("RUN_LIVE_API_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_API_TESTS=1 to run live Deepgram smoke tests.")
    if not AppConfig.DEEPGRAM_API_KEY:
        pytest.fail(
            "RUN_LIVE_API_TESTS is enabled but DEEPGRAM_API_KEY is not configured."
        )


def test_live_deepgram_flux_stream_connects_without_audio():
    """API-STT-001: verify Deepgram key, model, network, and WebSocket handshake."""
    _require_live_api_opt_in()
    errors: list[tuple[str, str]] = []
    session = DeepgramSession(
        api_key=AppConfig.DEEPGRAM_API_KEY,
        model=AppConfig.DEEPGRAM_MODEL,
        sample_rate=AppConfig.STT_SAMPLE_RATE,
        turn_end_silence_ms=AppConfig.TURN_END_SILENCE_MS,
        switch_response_min_ms=AppConfig.SWITCH_RESPONSE_MIN_MS,
        callbacks=TranscriptionCallbacks(
            on_started=lambda _speech_id: None,
            on_partial=lambda _speech_id, _text: None,
            on_final=lambda _speech_id, _text: None,
            on_error=lambda code, message: errors.append((code, message)),
        ),
    )

    session.start()
    deadline = time.monotonic() + CONNECT_TIMEOUT_SECONDS
    while not session.is_connected and not errors and time.monotonic() < deadline:
        time.sleep(0.05)

    try:
        assert not errors, f"Deepgram stream failed: {errors}"
        assert session.is_connected, "Deepgram stream did not connect before timeout"
    finally:
        session.stop()
