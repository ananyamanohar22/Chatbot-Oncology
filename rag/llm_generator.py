"""
rag/llm_generator.py
LLM-based response generator using Groq API.

Generates personalized, empathetic responses based on:
- Current therapeutic state
- Patient's emotional state
- Session context and history
- Therapeutic guidelines
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv
from groq import Groq

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LLMGenerator:
    """Generates responses using Groq LLM."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize LLM generator.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in environment or .env file")

        self.client = Groq(api_key=self.api_key)
        logger.info("[LLM] Groq API client initialized")

    def generate_response(self, rag_context: Dict[str, Any]) -> str:
        """
        Generate a personalized response using Groq.

        Args:
            rag_context: Context retrieved by RAG retriever

        Returns:
            Generated response text
        """
        # Build the prompt with context
        prompt = self._build_prompt(rag_context)

        logger.info("[LLM] Generating response with Groq")

        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(rag_context)

            # Groq API expects system in messages array with role "system"
            message = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Fast Groq model
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            response_text = message.choices[0].message.content
            logger.info("[LLM] Response generated successfully")
            return response_text

        except Exception as e:
            logger.error(f"[LLM] Error generating response: {str(e)}")
            logger.info("[LLM] Falling back to library content")
            # Fallback to library content if LLM fails
            fallback = self._fallback_response(rag_context)
            logger.info(f"[LLM] Fallback response: {fallback[:100]}...")
            return fallback

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with guidelines and context."""
        state = context.get("state_info", {})
        emotion = context.get("emotional_context", {})
        guidelines = emotion.get("recommendations", [])

        system_prompt = f"""You are a compassionate therapeutic chatbot supporting oncology patients.

        Current State: {state.get('state_name')}
        State Description: {state.get('state_description')}
        
        Patient's Emotional State: {emotion.get('emotion_state')}
        
        Therapeutic Guidelines:
        {chr(10).join(f"- {g}" for g in guidelines)}
        
        IMPORTANT RULES:
        1. Be warm, empathetic, and supportive
        2. Never give medical advice - always defer to healthcare providers
        3. Keep responses concise (2-3 sentences)
        4. Match the patient's pace and comfort level
        5. Use grounding and relaxation techniques when appropriate
        6. Validate emotions without judgment
        7. Emphasize patient agency and control
        8. Stay within the therapeutic context of the current state
        
        Respond naturally as if continuing a therapeutic conversation."""

        return system_prompt

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build user prompt with context."""
        history = context.get("session_history", [])
        user_message = context.get("user_message", "")

        # Build context about recent conversation
        history_text = ""
        if history:
            history_text = "Recent conversation:\n"
            for msg in history[-3:]:  # Last 3 messages
                role = "Patient" if msg.get("role") == "user" else "Therapist"
                content = msg.get("content", "")[:100]  # Truncate long messages
                history_text += f"{role}: {content}\n"

        prompt = f"""{history_text}
Now the patient says: "{user_message}"

Respond with a brief, supportive, therapeutic response."""

        return prompt

    def _fallback_response(self, context: Dict[str, Any]) -> str:
        """Fallback response if LLM fails."""
        library = context.get("library_context", [])
        state = context.get("state_info", {})
        emotion = context.get("emotional_context", {}).get("emotion_state", "calm")

        # Find relevant library content for current state
        for item in library:
            if item.get("metadata", {}).get("state") == state.get("state_code"):
                body = item.get("body")
                if body:
                    return body

        # If no library item found, provide generic response
        state_code = state.get("state_code", "")
        state_name = state.get("state_name", "")

        # Generic responses by state
        fallback_responses = {
            "guided_intro": "Hello, I'm RelaxBot. How are you feeling right now?",
            "guided_breathing": "Let's focus on your breathing. Take slow, deep breaths and notice how your body relaxes with each exhale.",
            "guided_observation": "Continue with your natural breathing. You're doing wonderfully.",
            "guided_countdown": "Imagine yourself descending deeper into relaxation with each number. You're safe and peaceful.",
            "guided_imagery": "Visualize your safe place. Feel the peace and healing it brings you.",
            "guided_hindsight": "Thank you for this journey. You've done beautiful work today.",
        }

        return fallback_responses.get(state_code, "I'm here to support you. Please continue at your own pace.")


# Singleton instance
llm_generator = None


def get_llm_generator() -> LLMGenerator:
    """Get or create LLM generator singleton."""
    global llm_generator
    if llm_generator is None:
        llm_generator = LLMGenerator()
    return llm_generator