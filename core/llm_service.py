"""
core/llm_service.py — Centralized LLM access via Groq API
All agents and tools call this service instead of Groq directly.
"""
import os
from typing import Optional, Dict, List
from groq import Groq
from core.config import (
    GROQ_API_KEY, LLM_CHAT_MODEL, LLM_ANALYSIS_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS
)


class LLMService:

    def __init__(self, api_key: str = None, database=None):
        self.api_key = api_key or GROQ_API_KEY
        self.database = database
        self.chat_model = LLM_CHAT_MODEL           # llama-3.1-8b-instant
        self.analysis_model = LLM_ANALYSIS_MODEL    # llama-3.3-70b-versatile

        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ No API key. Using rule-based fallback responses.")

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        include_employee_data: bool = False,
        model: str = None
    ) -> str:
        """
        General-purpose LLM call.
        - model: defaults to chat_model. Pass analysis_model for deep tasks.
        - include_employee_data: appends DB employee summary to system prompt.
        """
        if not self.client:
            return self._fallback_response(prompt)

        try:
            messages = []

            full_system = system_prompt
            if include_employee_data and self.database:
                full_system += f"\n\n{self.database.get_employee_summary()}"
                full_system += "\nYou have access to the current employee database. "
                full_system += "Use this information to answer specific questions about employees."

            if full_system:
                messages.append({"role": "system", "content": full_system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=model or self.chat_model,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"LLM Error: {e}")
            return self._fallback_response(prompt)

    # Alias kept for backward compatibility with existing code
    def ask_question(self, prompt: str) -> str:
        return self.generate_response(prompt)

    def generate_json_response(
        self, prompt: str, system_prompt: str = ""
    ) -> str:
        """Use the deeper analysis model. Caller parses JSON from response."""
        return self.generate_response(
            prompt, system_prompt, model=self.analysis_model
        )

    def chat_with_history(
        self, messages: List[Dict], model: str = None
    ) -> str:
        """Send a full message list (for multi-turn conversations)."""
        if not self.client:
            return self._fallback_response(messages[-1].get("content", ""))

        try:
            response = self.client.chat.completions.create(
                model=model or self.chat_model,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return "I'm having trouble processing that. Please try again."

    # ─────────── Fallback (rule-based when no API key) ───────────

    def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        # Try employee lookup from DB
        if self.database and ("employee" in prompt_lower or "who is" in prompt_lower):
            for word in prompt.split():
                emp = self.database.search_employee_by_name(word)
                if emp:
                    return (
                        f"{emp.name} (ID: {emp.employee_id}) works as {emp.position} "
                        f"in {emp.department} department. Email: {emp.email}. "
                        f"Leave balance: Casual: {emp.leave_balance.get('Casual Leave', 0)}, "
                        f"Sick: {emp.leave_balance.get('Sick Leave', 0)}, "
                        f"Annual: {emp.leave_balance.get('Annual Leave', 0)} days."
                    )

        if "leave" in prompt_lower and "balance" in prompt_lower:
            return "You can check your leave balance in the employee portal or contact HR."
        elif "policy" in prompt_lower:
            return "Please refer to the employee handbook or ask HR for specific policy details."
        return "I understand your query. Please contact HR for detailed assistance."
