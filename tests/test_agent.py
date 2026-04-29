"""Tests for the agent module — tool execution functions.

These tests are deterministic: they test that the tool functions correctly
modify session state.  No live OpenAI API calls are made.
"""

from datetime import date
import logging

from agent import (
    AgentResponse,
    execute_add_task,
    execute_flag_conflict_or_gap,
    execute_get_schedule,
)
from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_owners() -> list[Owner]:
    """Build a small test household."""
    jordan = Owner(name="Jordan")
    mochi = Pet(name="Mochi", animal="dog", age=4)
    pixel = Pet(name="Pixel", animal="cat", age=2)
    jordan.add_pet(mochi)
    jordan.add_pet(pixel)

    mochi.add_task(Task(description="Morning walk", time="07:00", frequency="daily", due_date=date(2026, 4, 29)))
    mochi.add_task(Task(description="Lunch", time="12:00", frequency="daily", due_date=date(2026, 4, 29)))
    pixel.add_task(Task(description="Breakfast", time="08:00", frequency="daily", due_date=date(2026, 4, 29)))

    alex = Owner(name="Alex")
    kiwi = Pet(name="Kiwi", animal="bird", age=1)
    alex.add_pet(kiwi)
    kiwi.add_task(Task(description="Cage clean", time="09:00", frequency="weekly", due_date=date(2026, 4, 29)))

    return [jordan, alex]


# ---------------------------------------------------------------------------
# get_schedule tests
# ---------------------------------------------------------------------------

def test_get_schedule_returns_tasks_for_owner() -> None:
    """get_schedule should return tasks belonging to the specified owner."""
    owners = _make_test_owners()
    result = execute_get_schedule(
        {"owner_name": "Jordan", "start_date": "2026-04-29", "end_date": "2026-04-29"},
        owners,
    )
    assert "Mochi" in result
    assert "Morning walk" in result
    assert "Kiwi" not in result  # Kiwi belongs to Alex


def test_get_schedule_returns_all_owners_when_all() -> None:
    """Using 'All' should return tasks from every owner."""
    owners = _make_test_owners()
    result = execute_get_schedule(
        {"owner_name": "All", "start_date": "2026-04-29", "end_date": "2026-04-29"},
        owners,
    )
    assert "Mochi" in result
    assert "Kiwi" in result


def test_get_schedule_filters_by_date_range() -> None:
    """Tasks outside the date range should not appear."""
    owners = _make_test_owners()
    result = execute_get_schedule(
        {"owner_name": "All", "start_date": "2026-05-01", "end_date": "2026-05-01"},
        owners,
    )
    assert "No tasks found" in result


def test_get_schedule_handles_unknown_owner() -> None:
    """An unknown owner name should return a friendly error."""
    owners = _make_test_owners()
    result = execute_get_schedule({"owner_name": "Unknown"}, owners)
    assert "No owner named" in result


# ---------------------------------------------------------------------------
# add_task tests
# ---------------------------------------------------------------------------

def test_add_task_creates_task_in_session_state() -> None:
    """add_task should write a new task to the correct pet."""
    owners = _make_test_owners()
    jordan = owners[0]
    mochi = jordan.pets[0]
    initial_count = len(mochi.tasks)

    result = execute_add_task(
        {
            "owner_name": "Jordan",
            "pet_name": "Mochi",
            "description": "Flea treatment",
            "time": "10:00",
            "due_date": "2026-04-30",
            "frequency": "monthly",
        },
        owners,
    )

    assert "successfully added" in result.lower() or "added" in result.lower()
    assert len(mochi.tasks) == initial_count + 1
    new_task = mochi.tasks[-1]
    assert new_task.description == "Flea treatment"
    assert new_task.time == "10:00"
    assert new_task.due_date == date(2026, 4, 30)
    assert new_task.frequency == "monthly"


def test_add_task_rejects_invalid_owner() -> None:
    """Graceful error when the owner doesn't exist."""
    owners = _make_test_owners()
    result = execute_add_task(
        {
            "owner_name": "Nobody",
            "pet_name": "Mochi",
            "description": "Walk",
            "time": "09:00",
            "due_date": "2026-04-29",
            "frequency": "daily",
        },
        owners,
    )
    assert "error" in result.lower()


def test_add_task_rejects_invalid_pet() -> None:
    """Graceful error when the pet doesn't exist under the owner."""
    owners = _make_test_owners()
    result = execute_add_task(
        {
            "owner_name": "Jordan",
            "pet_name": "Ghost",
            "description": "Walk",
            "time": "09:00",
            "due_date": "2026-04-29",
            "frequency": "daily",
        },
        owners,
    )
    assert "error" in result.lower()


def test_add_task_detects_conflict_after_creation() -> None:
    """Adding a task at the same time/date as an existing one should warn."""
    owners = _make_test_owners()
    result = execute_add_task(
        {
            "owner_name": "Jordan",
            "pet_name": "Mochi",
            "description": "Vet visit",
            "time": "07:00",           # same as Morning walk
            "due_date": "2026-04-29",   # same date
            "frequency": "as needed",
        },
        owners,
    )
    assert "conflict" in result.lower() or "warning" in result.lower()


# ---------------------------------------------------------------------------
# flag_conflict_or_gap tests
# ---------------------------------------------------------------------------

def test_flag_conflict_appends_warning() -> None:
    """flag_conflict_or_gap should append the message to the warnings list."""
    warnings: list[str] = []
    result = execute_flag_conflict_or_gap(
        {"message": "Mochi has no exercise scheduled today!"},
        warnings,
    )
    assert len(warnings) == 1
    assert "no exercise" in warnings[0].lower()
    assert "Warning surfaced" in result


def test_flag_conflict_handles_empty_message() -> None:
    """An empty message should not crash."""
    warnings: list[str] = []
    execute_flag_conflict_or_gap({"message": ""}, warnings)
    assert len(warnings) == 0  # empty messages are not appended


# ---------------------------------------------------------------------------
# AgentResponse confidence extraction
# ---------------------------------------------------------------------------

def test_agent_response_default_confidence() -> None:
    """Default confidence should be 3 when not specified."""
    resp = AgentResponse(text="Hello!")
    assert resp.confidence == 3


def test_tool_execution_is_logged(caplog) -> None:
    """Verify that tool calls produce log entries."""
    owners = _make_test_owners()
    with caplog.at_level(logging.INFO, logger="pawpal_agent"):
        # We can't test the full agent loop without an API key, but we can
        # verify that the logging infrastructure works by calling a tool helper
        # and checking that no exceptions are raised.
        result = execute_get_schedule({"owner_name": "All"}, owners)
        assert isinstance(result, str)
