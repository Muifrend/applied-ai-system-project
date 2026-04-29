"""PawPal+ AI Agent — GPT-4o powered agent with three tools that reads/writes
the same Streamlit session_state the dashboard uses.

Tools:
    get_schedule   — read current tasks for an owner in a date range
    add_task        — write a new task to a specific pet
    flag_conflict_or_gap — surface a warning to the UI

Every invocation, tool call, and result is logged to ``pawpal.log``.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime

from openai import OpenAI

from src.knowledge_base import KnowledgeBase
from src.pawpal_system import Owner, Pet, Scheduler, Task

# ---------------------------------------------------------------------------
# Logging setup — writes to pawpal.log with timestamps
# ---------------------------------------------------------------------------

_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pawpal.log")

logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pawpal_agent")

# Also log to console so Streamlit terminal shows activity
_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(_console)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
_MAX_TOOL_ITERATIONS = 5

# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function calling schema)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": (
                "Retrieve the current task schedule for a specific owner or all owners. "
                "Returns a list of tasks with pet name, description, time, due date, "
                "frequency, and completion status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner_name": {
                        "type": "string",
                        "description": "Owner name to filter by, or 'All' for every owner.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start of date range in YYYY-MM-DD format. Defaults to today.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End of date range in YYYY-MM-DD format. Defaults to today.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": (
                "Create a new care task for a specific pet.  The task is written "
                "directly into the live schedule that the dashboard displays."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner_name": {
                        "type": "string",
                        "description": "Name of the owner who owns the pet.",
                    },
                    "pet_name": {
                        "type": "string",
                        "description": "Name of the pet to assign the task to.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Short description of the task (e.g. 'Flea treatment').",
                    },
                    "time": {
                        "type": "string",
                        "description": "Time in HH:MM 24-hour format (e.g. '09:00').",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format.",
                    },
                    "frequency": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "as needed"],
                        "description": "How often the task recurs.",
                    },
                },
                "required": ["owner_name", "pet_name", "description", "time", "due_date", "frequency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_conflict_or_gap",
            "description": (
                "Surface a warning or informational message to the user through the UI. "
                "Use this when you detect a scheduling conflict, a gap in care, or want "
                "to alert the user about something important."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The warning or informational message to display.",
                    },
                },
                "required": ["message"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Agent response container
# ---------------------------------------------------------------------------


@dataclass
class AgentResponse:
    """Container for the final agent output."""

    text: str
    confidence: int = 3
    tool_calls_made: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool execution helpers
# ---------------------------------------------------------------------------


def _find_owner(owners: list[Owner], name: str) -> Owner | None:
    for owner in owners:
        if owner.name.lower() == name.lower():
            return owner
    return None


def _find_pet(owner: Owner, name: str) -> Pet | None:
    for pet in owner.pets:
        if pet.name.lower() == name.lower():
            return pet
    return None


def _parse_date(s: str | None) -> date:
    if not s:
        return date.today()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def execute_get_schedule(args: dict, owners: list[Owner]) -> str:
    """Read tasks from session state matching owner + date range."""
    owner_name = args.get("owner_name", "All")
    start = _parse_date(args.get("start_date"))
    end = _parse_date(args.get("end_date"))
    if end < start:
        end = start

    target_owners = owners if owner_name.lower() == "all" else [o for o in owners if o.name.lower() == owner_name.lower()]
    if not target_owners:
        return f"No owner named '{owner_name}' found."

    lines: list[str] = []
    for owner in target_owners:
        scheduler = Scheduler(owner=owner)
        for task in scheduler.organize_tasks(include_completed=True):
            if start <= task.due_date <= end:
                pet_name = "unknown"
                for pet in owner.pets:
                    if any(t is task for t in pet.tasks):
                        pet_name = pet.name
                        break
                status = "✅ done" if task.is_completed else "⬜ pending"
                lines.append(
                    f"[{owner.name}] {pet_name} | {task.description} | "
                    f"{task.time} | {task.due_date.isoformat()} | {task.frequency} | {status}"
                )
    return "\n".join(lines) if lines else "No tasks found for the given criteria."


def execute_add_task(args: dict, owners: list[Owner]) -> str:
    """Write a new task into session state."""
    owner = _find_owner(owners, args["owner_name"])
    if owner is None:
        return f"Error: Owner '{args['owner_name']}' not found."

    pet = _find_pet(owner, args["pet_name"])
    if pet is None:
        return f"Error: Pet '{args['pet_name']}' not found under owner '{owner.name}'."

    due = _parse_date(args.get("due_date"))
    new_task = Task(
        description=args["description"],
        time=args["time"],
        frequency=args["frequency"],
        due_date=due,
    )

    # Check for conflicts before adding
    for existing in pet.get_tasks(include_completed=False):
        if existing.due_date == new_task.due_date and existing.time == new_task.time:
            pet.add_task(new_task)
            return (
                f"Task '{new_task.description}' added to {pet.name}, but WARNING: "
                f"conflict detected with existing task '{existing.description}' at "
                f"{existing.time} on {existing.due_date.isoformat()}."
            )

    pet.add_task(new_task)
    return (
        f"Task '{new_task.description}' successfully added to {pet.name} "
        f"at {new_task.time} on {new_task.due_date.isoformat()} ({new_task.frequency})."
    )


def execute_flag_conflict_or_gap(args: dict, agent_warnings: list[str]) -> str:
    """Append a warning message to the UI warnings list."""
    message = args.get("message", "")
    if message:
        agent_warnings.append(message)
    return f"Warning surfaced to user: {message}"


# ---------------------------------------------------------------------------
# Schedule snapshot builder
# ---------------------------------------------------------------------------


def build_schedule_snapshot(owners: list[Owner]) -> str:
    """Create a human-readable summary of the current schedule for the prompt."""
    lines: list[str] = ["Current Schedule:"]
    for owner in owners:
        lines.append(f"\nOwner: {owner.name}")
        if not owner.pets:
            lines.append("  (no pets)")
            continue
        for pet in owner.pets:
            lines.append(f"  Pet: {pet.name} ({pet.animal}, age {pet.age})")
            pending = pet.get_tasks(include_completed=False)
            if not pending:
                lines.append("    No pending tasks.")
            else:
                for task in sorted(pending, key=lambda t: (t.due_date, t.time)):
                    lines.append(
                        f"    - {task.description} at {task.time} on "
                        f"{task.due_date.isoformat()} ({task.frequency})"
                    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are PawPal AI, a friendly and knowledgeable pet-care scheduling assistant \
embedded in the PawPal+ app.

Your capabilities:
1. **Read the schedule** using the get_schedule tool to see current tasks.
2. **Add tasks** using the add_task tool to create new care activities.
3. **Flag warnings** using the flag_conflict_or_gap tool to alert the user \
about scheduling conflicts or gaps in care.

Rules:
- Ground your suggestions in the pet-care knowledge provided below. \
If the knowledge base has relevant information, reference it.
- When adding tasks, always confirm what you did in your response.
- If you detect a conflict after adding a task, use flag_conflict_or_gap.
- If you cannot fulfill a request (e.g., deleting tasks, modifying owners), \
explain what you can do instead. Do NOT hallucinate capabilities.
- Keep responses concise and helpful.
- At the END of every response, output a confidence score in exactly this \
format on its own line: [Confidence: X/5] where X is 1-5.
  - 5 = fully confident, grounded in knowledge base and verified schedule
  - 3 = reasonable suggestion but not fully verified
  - 1 = unsure, recommend consulting a veterinarian

Today's date is {today}.
"""


# ---------------------------------------------------------------------------
# Main agent class
# ---------------------------------------------------------------------------


class PawPalAgent:
    """GPT-4o agent with tool use for PawPal+ scheduling."""

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.client = OpenAI()
        self.kb = knowledge_base

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        owners: list[Owner],
        chat_history: list[dict[str, str]],
        agent_warnings: list[str] | None = None,
    ) -> AgentResponse:
        """Execute the full agent loop and return a structured response."""
        if agent_warnings is None:
            agent_warnings = []

        logger.info("Agent invocation — user message: %s", user_message)

        # 1. RAG retrieval
        rag_chunks = self.kb.query(user_message, n_results=3)
        rag_context = "\n\n".join(rag_chunks) if rag_chunks else "(no relevant knowledge found)"
        logger.info("RAG retrieved %d chunks", len(rag_chunks))

        # 2. Build messages
        system = _SYSTEM_PROMPT.format(today=date.today().isoformat())
        system += f"\n\n--- Pet-Care Knowledge ---\n{rag_context}\n"
        system += f"\n--- Current Schedule Snapshot ---\n{build_schedule_snapshot(owners)}\n"

        messages: list[dict] = [{"role": "system", "content": system}]

        # Append prior chat history (keep recent turns only to stay within context)
        for msg in chat_history[-20:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        # 3. Agent loop
        tool_calls_made: list[str] = []

        for iteration in range(_MAX_TOOL_ITERATIONS):
            response = self.client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=1024,
            )

            choice = response.choices[0]

            # If no tool calls, we're done
            if choice.finish_reason != "tool_calls" and not choice.message.tool_calls:
                break

            # Handle tool calls
            if choice.message.tool_calls:
                messages.append(choice.message)  # assistant message with tool_calls

                for tool_call in choice.message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    logger.info("Tool call [%d]: %s(%s)", iteration, fn_name, json.dumps(fn_args))

                    # Execute the tool
                    result = self._execute_tool(fn_name, fn_args, owners, agent_warnings)
                    logger.info("Tool result [%d]: %s", iteration, result[:200])

                    tool_calls_made.append(fn_name)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                break

        # 4. Get the final text response
        final_text = choice.message.content or "I wasn't able to generate a response."

        # 5. Extract confidence score
        confidence = self._extract_confidence(final_text)

        logger.info("Agent response (confidence=%d): %s", confidence, final_text[:200])

        return AgentResponse(
            text=final_text,
            confidence=confidence,
            tool_calls_made=tool_calls_made,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_tool(
        self,
        name: str,
        args: dict,
        owners: list[Owner],
        agent_warnings: list[str],
    ) -> str:
        """Dispatch a tool call to the correct handler."""
        if name == "get_schedule":
            return execute_get_schedule(args, owners)
        if name == "add_task":
            return execute_add_task(args, owners)
        if name == "flag_conflict_or_gap":
            return execute_flag_conflict_or_gap(args, agent_warnings)
        return f"Error: Unknown tool '{name}'."

    @staticmethod
    def _extract_confidence(text: str) -> int:
        """Parse ``[Confidence: X/5]`` from the response text."""
        match = re.search(r"\[Confidence:\s*(\d)/5\]", text)
        if match:
            return max(1, min(5, int(match.group(1))))
        return 3  # default if agent didn't include it
