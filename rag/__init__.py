"""
rag/
RAG (Retrieval Augmented Generation) system for response retrieval and synthesis.

Modules:
- retriever.py: Retrieves response templates based on patient queries
- llm_generator.py: Synthesizes final responses using LLM
"""

from .retriever import RAGRetriever
from .llm_generator import LLMGenerator, get_llm_generator

__all__ = ["RAGRetriever", "LLMGenerator", "get_llm_generator"]
