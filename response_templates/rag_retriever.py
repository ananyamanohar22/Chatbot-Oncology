"""
response_templates/rag_retriever.py
RAG Retriever — hybrid search (pattern matching + semantic embeddings) for response templates.

Two-stage retrieval:
1. Pattern Matching: Fast keyword/regex matching on patient query
2. Semantic Search: Embedding-based similarity if patterns don't match well

Returns top-ranked response template for the patient's query.
"""

import logging
import re
from typing import Optional
from db import SessionLocal
from response_templates.models import ResponseTemplate

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Hybrid RAG retriever for patient query → response template."""

    def __init__(self):
        self.db = SessionLocal()

    def __del__(self):
        """Cleanup database session."""
        if hasattr(self, 'db'):
            self.db.close()

    def retrieve(self, patient_query: str, intent_category: Optional[str] = None) -> Optional[ResponseTemplate]:
        """
        Retrieve the best matching response template for a patient query.

        Uses hybrid approach:
        1. Pattern matching on keywords (fast, deterministic)
        2. Semantic search on embeddings (slow, flexible)

        Returns top-ranked result.

        Args:
            patient_query: What the patient said (e.g., "I'm not ready")
            intent_category: Optional category filter (e.g., "hesitation", "fear")

        Returns:
            ResponseTemplate with best match, or None if no match found
        """
        try:
            # Stage 1: Pattern matching (keywords)
            keyword_matches = self._pattern_match(patient_query, intent_category)

            if keyword_matches:
                logger.info(f"[RAG] Pattern match found: {keyword_matches.query_pattern}")
                return keyword_matches

            # Stage 2: Semantic search (fallback if no keyword match)
            semantic_match = self._semantic_search(patient_query, intent_category)

            if semantic_match:
                logger.info(f"[RAG] Semantic match found: {semantic_match.query_pattern}")
                return semantic_match

            logger.warning(f"[RAG] No match found for query: {patient_query}")
            return None

        except Exception as e:
            logger.error(f"[RAG] Error retrieving template: {str(e)}")
            return None

    def _pattern_match(
        self, query: str, intent_category: Optional[str] = None
    ) -> Optional[ResponseTemplate]:
        """
        Stage 1: Fast keyword/pattern matching.

        Searches through response templates' keywords and scores matches.
        Returns highest-scored match.

        Args:
            query: Patient query text
            intent_category: Optional category filter

        Returns:
            Best matching ResponseTemplate or None
        """
        # Normalize query for matching
        query_lower = query.lower().strip()

        try:
            # Build base query
            base_query = self.db.query(ResponseTemplate).filter(
                ResponseTemplate.is_active == True
            )

            # Apply category filter if provided
            if intent_category:
                base_query = base_query.filter(
                    ResponseTemplate.intent_category == intent_category
                )

            templates = base_query.all()

            if not templates:
                return None

            # Score each template's keyword matches
            best_match = None
            best_score = 0.0

            for template in templates:
                score = 0.0

                # Check if query matches any keywords
                if template.keywords:
                    for keyword in template.keywords:
                        keyword_lower = keyword.lower().strip()

                        # Exact substring match (highest score)
                        if keyword_lower in query_lower:
                            score += 1.0

                        # Partial word match
                        elif self._levenshtein_distance(keyword_lower, query_lower) <= 2:
                            score += 0.7

                # Apply base relevance score
                if score > 0:
                    score *= template.relevance_score

                    if score > best_score:
                        best_score = score
                        best_match = template

            return best_match if best_score > 0.3 else None

        except Exception as e:
            logger.error(f"[RAG] Pattern matching error: {str(e)}")
            return None

    def _semantic_search(
        self, query: str, intent_category: Optional[str] = None
    ) -> Optional[ResponseTemplate]:
        """
        Stage 2: Semantic search using embeddings (fallback).

        Currently a placeholder — in production, would:
        1. Generate embedding for patient query
        2. Compare against stored embeddings
        3. Return closest match

        TODO: Implement with OpenAI embeddings or similar.

        Args:
            query: Patient query text
            intent_category: Optional category filter

        Returns:
            Best matching ResponseTemplate or None
        """
        logger.debug(f"[RAG] Semantic search placeholder for: {query}")
        # TODO: Implement embedding-based search
        # This would require:
        # 1. OpenAI embeddings API (or similar)
        # 2. pgvector extension in PostgreSQL
        # 3. Vector similarity comparison
        return None

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """
        Simple Levenshtein distance for fuzzy string matching.

        Returns the minimum edits (insertions, deletions, substitutions)
        needed to transform s1 into s2.
        """
        if len(s1) < len(s2):
            return RAGRetriever._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def get_all_templates(self, active_only: bool = True) -> list[ResponseTemplate]:
        """Get all response templates."""
        query = self.db.query(ResponseTemplate)
        if active_only:
            query = query.filter(ResponseTemplate.is_active == True)
        return query.all()

    def create_template(
        self,
        query_pattern: str,
        intent_category: str,
        responses: list[str],
        keywords: list[str],
        description: str = "",
        relevance_score: float = 0.8,
    ) -> ResponseTemplate:
        """Create a new response template."""
        template = ResponseTemplate(
            query_pattern=query_pattern,
            intent_category=intent_category,
            description=description,
            responses=responses,
            keywords=keywords,
            relevance_score=relevance_score,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        logger.info(f"[RAG] Created template: {query_pattern}")
        return template
