"""Wrapper for GitHub Copilot SDK CopilotClient with skill testing helpers.

This module provides a high-level interface for launching Copilot sessions,
sending skill commands, and collecting structured results.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from copilot import CopilotClient, PermissionHandler


@dataclass
class SkillResult:
    """Result from executing a skill command."""

    content: str
    """Raw text content from the assistant."""

    events: list[dict] = field(default_factory=list)
    """All events received during execution."""

    def contains_pattern(self, pattern: str) -> bool:
        """Check if content matches a regex pattern."""
        return bool(re.search(pattern, self.content, re.IGNORECASE | re.MULTILINE))

    def contains_section(self, heading: str) -> bool:
        """Check if content contains a markdown heading."""
        pattern = rf"^#+\s*{re.escape(heading)}"
        return self.contains_pattern(pattern)

    def extract_section(self, heading: str) -> str | None:
        """Extract content under a markdown heading."""
        pattern = rf"^(#+)\s*{re.escape(heading)}.*?\n(.*?)(?=^\1\s|\Z)"
        match = re.search(pattern, self.content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        return match.group(2).strip() if match else None

    def has_cp_notation(self) -> bool:
        """Check if content contains Customer Problem structured notation."""
        # CP notation: [Subject] [must/expects/hopes] [Object] [Penalty]
        return self.contains_pattern(
            r"(must|expects?|hopes?|should|have to|is required to)"
        )

    def has_cn_notation(self) -> bool:
        """Check if content contains Customer Needs structured notation."""
        # CN notation: [Noun] needs [System] to [Verb] [Object]
        return self.contains_pattern(r"needs?\s+.*?\s+to\s+")

    def has_fr_notation(self) -> bool:
        """Check if content contains Functional Requirements notation."""
        # FR notation: The [System] shall [Verb] [Object]
        return self.contains_pattern(r"(shall|should)\s+")


class SkillTestClient:
    """High-level client for testing Copilot skills."""

    def __init__(
        self,
        skill_dir: str | None = None,
        model: str = "gpt-5",
        timeout: float = 120.0,
    ):
        """Initialize the skill test client.

        Args:
            skill_dir: Path to the skills directory. If None, uses SKILL_DIR env var.
            model: Model to use for sessions.
            timeout: Maximum time to wait for skill execution.
        """
        self.skill_dir = skill_dir or os.environ.get(
            "SKILL_DIR", r"C:\work\Problem-Based-SRS"
        )
        self.model = model
        self.timeout = timeout
        self._client: CopilotClient | None = None

    async def __aenter__(self) -> SkillTestClient:
        """Start the client."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the client."""
        await self.stop()

    async def start(self) -> None:
        """Start the Copilot client."""
        self._client = CopilotClient({
            "cwd": self.skill_dir,
            "log_level": "warning",
            "use_logged_in_user": True,
        })
        await self._client.start()

    async def stop(self) -> None:
        """Stop the Copilot client."""
        if self._client:
            await self._client.stop()
            self._client = None

    async def execute_skill(
        self,
        prompt: str,
        system_message: str | None = None,
        on_event: Callable[[dict], None] | None = None,
    ) -> SkillResult:
        """Execute a skill command and collect the result.

        Args:
            prompt: The prompt to send (e.g., "/cp" or business context).
            system_message: Optional system message to prepend.
            on_event: Optional callback for events.

        Returns:
            SkillResult with the collected content and events.
        """
        if not self._client:
            raise RuntimeError("Client not started. Call start() first.")

        session_config = {
            "model": self.model,
            "on_permission_request": PermissionHandler.approve_all,
        }
        if system_message:
            session_config["system_message"] = {"content": system_message}

        session = await self._client.create_session(session_config)

        result_content: list[str] = []
        events: list[dict] = []
        done = asyncio.Event()

        def handle_event(event):
            events.append({"type": str(event.type.value), "data": getattr(event, "data", None)})
            if on_event:
                on_event(event)
            if event.type.value == "assistant.message":
                if hasattr(event.data, "content"):
                    result_content.append(event.data.content)
            elif event.type.value == "session.idle":
                done.set()

        session.on(handle_event)

        await session.send({"prompt": prompt})

        try:
            await asyncio.wait_for(done.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            pass  # Return what we have

        await session.destroy()

        return SkillResult(
            content="\n".join(result_content),
            events=events,
        )

    async def test_skill_response(
        self,
        skill_command: str,
        context: str,
        expected_patterns: list[str] | None = None,
        expected_sections: list[str] | None = None,
    ) -> tuple[SkillResult, list[str]]:
        """Test a skill and check for expected patterns/sections.

        Args:
            skill_command: The skill command (e.g., "/cp", "/cn").
            context: Business context or input for the skill.
            expected_patterns: Regex patterns that should appear.
            expected_sections: Markdown sections that should exist.

        Returns:
            Tuple of (SkillResult, list of failed checks).
        """
        prompt = f"{skill_command}\n\n{context}" if context else skill_command
        result = await self.execute_skill(prompt)

        failures: list[str] = []

        if expected_patterns:
            for pattern in expected_patterns:
                if not result.contains_pattern(pattern):
                    failures.append(f"Missing pattern: {pattern}")

        if expected_sections:
            for section in expected_sections:
                if not result.contains_section(section):
                    failures.append(f"Missing section: {section}")

        return result, failures
