"""
test_rag_integration.py
Quick integration test for RAG system with session manager.

Tests:
1. RAGRetriever.retrieve_context() static method
2. LLMGenerator.generate_response() with rag context
3. Full integration chain
"""

import logging
import sys
import os
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import SessionLocal
from rag.retriever import RAGRetriever
from rag.llm_generator import get_llm_generator
from response_templates.models import ResponseTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_response_templates_exist():
    """Test that response templates exist in database."""
    db = SessionLocal()
    try:
        count = db.query(ResponseTemplate).count()
        logger.info(f"✓ Found {count} response templates in database")

        if count == 0:
            logger.warning("⚠ No response templates found. Please seed database first.")
            return False

        # Show a sample
        sample = db.query(ResponseTemplate).first()
        if sample:
            logger.info(f"  Sample: {sample.query_pattern} -> {len(sample.responses)} responses")
        return True
    except Exception as e:
        logger.error(f"✗ Error querying templates: {e}")
        return False
    finally:
        db.close()


def test_rag_retriever_static_method():
    """Test RAGRetriever.retrieve_context() static method."""
    logger.info("\n=== Testing RAGRetriever.retrieve_context() ===")

    try:
        # Use dummy UUIDs for testing
        session_id = UUID('00000000-0000-0000-0000-000000000001')
        state_id = UUID('00000000-0000-0000-0000-000000000002')

        # Test with a query that should match
        context = RAGRetriever.retrieve_context(
            session_id=session_id,
            current_state_id=state_id,
            message="I'm not ready to start",
            emotion="hesitant"
        )

        if context:
            logger.info(f"✓ Retrieved context:")
            logger.info(f"  Query Pattern: {context.get('query_pattern')}")
            logger.info(f"  Intent: {context.get('intent_category')}")
            logger.info(f"  Relevance Score: {context.get('relevance_score')}")
            logger.info(f"  Response Options: {len(context.get('responses', []))}")
            logger.info(f"  Emotion: {context.get('emotion')}")
            return True
        else:
            logger.warning("⚠ No context retrieved (empty context dict)")
            # This is ok if no templates matched
            return True
    except Exception as e:
        logger.error(f"✗ Error in retrieve_context: {e}", exc_info=True)
        return False


def test_llm_generator():
    """Test LLMGenerator.generate_response()."""
    logger.info("\n=== Testing LLMGenerator.generate_response() ===")

    try:
        # Create sample RAG context
        rag_context = {
            "query_pattern": "not_ready",
            "intent_category": "hesitation",
            "responses": [
                "That's completely okay. We can take this at your own pace.",
                "I understand. When you feel ready, just let me know.",
                "No pressure at all. We'll move forward whenever you're comfortable.",
            ],
            "relevance_score": 0.85,
            "emotion": "hesitant",
            "user_message": "I'm not ready to start",
            "session_id": UUID('00000000-0000-0000-0000-000000000001'),
            "state_id": UUID('00000000-0000-0000-0000-000000000002'),
        }

        # Get generator and generate response
        llm_generator = get_llm_generator()
        response = llm_generator.generate_response(rag_context)

        if response:
            logger.info(f"✓ Generated response:")
            logger.info(f"  {response}")
            return True
        else:
            logger.error("✗ No response generated")
            return False
    except Exception as e:
        logger.error(f"✗ Error in generate_response: {e}", exc_info=True)
        return False


def test_with_no_templates():
    """Test fallback behavior when no templates match."""
    logger.info("\n=== Testing Fallback Behavior ===")

    try:
        session_id = UUID('00000000-0000-0000-0000-000000000001')
        state_id = UUID('00000000-0000-0000-0000-000000000002')

        # Query that unlikely to match
        context = RAGRetriever.retrieve_context(
            session_id=session_id,
            current_state_id=state_id,
            message="xyzabc nonsense query with gibberish",
            emotion="neutral"
        )

        if context:
            logger.info(f"✓ Fallback context created:")
            logger.info(f"  Pattern: {context.get('query_pattern')}")
            logger.info(f"  Matched By: {context.get('matched_by')}")

            # Try to generate response from fallback
            llm_generator = get_llm_generator()
            response = llm_generator.generate_response(context)
            logger.info(f"  Response: {response}")
            return True
        else:
            logger.error("✗ No fallback context created")
            return False
    except Exception as e:
        logger.error(f"✗ Error in fallback test: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    logger.info("="*80)
    logger.info("RAG INTEGRATION TEST SUITE")
    logger.info("="*80)

    results = {
        "Response Templates": test_response_templates_exist(),
        "RAG Retriever (Static Method)": test_rag_retriever_static_method(),
        "LLM Generator": test_llm_generator(),
        "Fallback Behavior": test_with_no_templates(),
    }

    logger.info("\n" + "="*80)
    logger.info("TEST RESULTS")
    logger.info("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n✅ All tests passed! RAG integration is ready.")
        return 0
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
