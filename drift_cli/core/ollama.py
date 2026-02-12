"""Ollama client for local LLM inference."""

import json
from typing import Optional

import httpx
from pydantic import ValidationError

from drift_cli.core.memory import MemoryManager, enhance_prompt_with_memory
from drift_cli.models import Plan


class OllamaClient:
    """Client for interacting with local Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:1.5b",
        memory: Optional[MemoryManager] = None,
    ):
        self.base_url = base_url
        self.model = model
        self.client = httpx.Client(timeout=60.0)
        self.memory = memory or MemoryManager()

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def get_plan(self, query: str, context: Optional[str] = None, use_memory: bool = True) -> Plan:
        """
        Get a plan from Ollama for the given query.

        Args:
            query: User's natural language query
            context: Additional context (cwd, recent commands, etc.)
            use_memory: Whether to enhance prompt with learned user preferences

        Returns:
            Validated Plan object

        Raises:
            ValueError: If response is invalid or cannot be parsed
        """
        # Sanitize input to prevent prompt injection
        sanitized_query = self._sanitize_input(query)

        # Update memory context
        if use_memory and self.memory:
            self.memory.update_context(query=sanitized_query)

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(sanitized_query, context)

        # Enhance with memory if enabled
        if use_memory and self.memory:
            user_prompt = enhance_prompt_with_memory(user_prompt, self.memory)

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "format": "json",
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                        },
                    },
                    timeout=90.0,
                )
                response.raise_for_status()

                result = response.json()
                response_text = result.get("response", "").strip()

                # Parse and validate the JSON response
                try:
                    plan_data = json.loads(response_text)
                    plan = Plan(**plan_data)
                    return plan
                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        continue
                    raise ValueError(
                        "Invalid JSON from Ollama "
                        f"(attempt {attempt + 1}/{max_retries}): {str(e)[:100]}"
                    )
                except ValidationError as e:
                    error_details = str(e)[:200]
                    raise ValueError(f"Plan validation failed: {error_details}")

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    continue
                raise ValueError("Ollama request timed out after 90 seconds")
            except httpx.HTTPError as e:
                if attempt < max_retries - 1:
                    continue
                raise ValueError(f"Failed to communicate with Ollama: {str(e)[:100]}")

        raise ValueError("Failed to get plan after retries")

    def explain_command(self, command: str) -> str:
        """
        Get a detailed explanation of a command.

        Args:
            command: The shell command to explain

        Returns:
            Detailed explanation string
        """
        prompt = f"""Explain this shell command in detail:

Command: {command}

Provide:
1. What the command does (brief summary)
2. Breakdown of each flag/argument
3. Potential side effects or risks
4. Example output (if applicable)

Be concise but thorough."""

        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to get explanation: {e}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """You are Drift, a terminal assistant.
Convert natural language queries into safe, executable shell commands.

CRITICAL: You MUST respond with ONLY valid JSON matching this exact schema:
{
  "summary": "brief summary of what will be done",
  "risk": "low" | "medium" | "high",
  "commands": [
    {
      "command": "actual shell command",
      "description": "what this does",
      "dry_run": "optional dry-run version"
    }
  ],
  "explanation": "detailed explanation of the approach",
  "affected_files": ["optional", "list", "of", "files"],
  "clarification_needed": [
    {
      "question": "question text",
      "options": ["optional", "list"]
    }
  ]
}

RULES:
1. If the query is ambiguous, use "clarification_needed" field with questions
2. Always assess risk accurately (destructive ops = high, modifications = medium, reads = low)
3. Provide dry-run commands when possible (e.g., add -n flag for dry runs)
4. Be conservative: when uncertain, ask for clarification
5. Use common, portable shell commands (prefer standard Unix tools)
6. NEVER suggest rm -rf /, sudo rm -rf, or other destructive root operations
7. For file operations, always include affected_files list
8. Keep commands readable and well-explained

Respond with ONLY the JSON object, no other text."""

    def _build_user_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Build the user prompt with query and context."""
        prompt = f"User query: {query}"
        if context:
            prompt += f"\n\nContext:\n{context}"
        return prompt

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent prompt injection attacks.

        Args:
            text: User input to sanitize

        Returns:
            Sanitized text
        """
        # Remove potentially dangerous characters
        dangerous_chars = ["\x00", "\r", "\n\n\n"]  # null bytes, multiple newlines
        for char in dangerous_chars:
            if char in text:
                text = text.replace(char, " ")

        # Limit length to prevent DoS
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip()

    def close(self):
        """Close the HTTP client."""
        self.client.close()
