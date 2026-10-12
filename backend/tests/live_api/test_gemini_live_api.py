"""Opt-in smoke tests for the deployed Gemini judging integration.

These tests deliberately use the fixed shared fixture, never player data. They
are skipped by default because they require a real API key, consume provider
quota, and can fail when the provider is unavailable.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from app.config import AppConfig
from app.models import JudgeInput, JudgeResult, Scenario, TranscriptEvent
from app.services.judge_service import create_judge_service

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "shared" / "fixtures"


pytestmark = pytest.mark.live_api


def _require_live_api_opt_in() -> None:
    if os.getenv("RUN_LIVE_API_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_API_TESTS=1 to run live Gemini smoke tests.")
    if not AppConfig.GEMINI_API_KEY:
        pytest.fail(
            "RUN_LIVE_API_TESTS is enabled but GEMINI_API_KEY is not configured."
        )


def _fixture_judge_input() -> JudgeInput:
    with (FIXTURE_DIR / "mock-scenario.json").open(encoding="utf-8") as handle:
        scenario = Scenario.model_validate(json.load(handle))
    with (FIXTURE_DIR / "mock-transcript.json").open(encoding="utf-8") as handle:
        raw_events = json.load(handle)
    adapter = TypeAdapter(TranscriptEvent)
    return JudgeInput(
        scenario=scenario,
        transcript_events=[adapter.validate_python(event) for event in raw_events],
        switch_response_latencies={"switch_001": 380},
        round_duration_ms=60_000,
    )


def test_live_gemini_judge_returns_a_valid_structured_result():
    """API-JUDGE-001/002/003: verify live credentials, model, and schema."""
    _require_live_api_opt_in()

    result = create_judge_service(AppConfig).judge(_fixture_judge_input())

    assert isinstance(result, JudgeResult)
    assert result.player_a.highlight
    assert result.player_b.highlight
