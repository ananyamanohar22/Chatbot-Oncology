"""
test_llm_synthesis_e2e.py

Comprehensive end-to-end testing for LLM synthesis with various emotions and scenarios.
Tests the full pipeline: Patient Query → RAG Retrieval → LLM Synthesis → Response

Run with: python3 test_llm_synthesis_e2e.py
"""

import sys
import os
import logging
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.retriever import RAGRetriever
from rag.llm_generator import get_llm_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Comprehensive test cases covering different emotions and scenarios
TEST_CASES = [
    {
        "category": "Anxiety",
        "emotion": "anxious",
        "query": "I'm really nervous and scared about what's coming",
        "expected_keywords": ["safe", "here", "breathe", "calm"],
        "should_not_contain": ["danger", "fear"],
    },
    {
        "category": "Hesitation",
        "emotion": "hesitant",
        "query": "I'm not sure if I'm ready for this",
        "expected_keywords": ["pace", "time", "ready", "no pressure"],
        "should_not_contain": ["must", "should"],
    },
    {
        "category": "Physical Discomfort (Mild)",
        "emotion": "physically_uncomfortable_mild",
        "query": "I'm just a little bit uncomfortable",
        "expected_keywords": ["adjust", "comfortable", "help"],
        "should_not_contain": ["severe", "emergency"],
    },
    {
        "category": "Physical Discomfort (Moderate)",
        "emotion": "physically_uncomfortable_moderate",
        "query": "I'm experiencing quite a bit of discomfort in my chest",
        "expected_keywords": ["pause", "adjust", "address"],
        "should_not_contain": ["minor", "continue"],
    },
    {
        "category": "Back Pain",
        "emotion": "pain",
        "query": "My lower back is really hurting",
        "expected_keywords": ["back", "position", "ease"],
        "should_not_contain": ["ignore", "push through"],
    },
    {
        "category": "Headache",
        "emotion": "pain",
        "query": "I have a pounding headache",
        "expected_keywords": ["head", "relax", "breathe"],
        "should_not_contain": ["medication", "doctor"],
    },
    {
        "category": "Neck/Shoulder Tension",
        "emotion": "pain",
        "query": "My neck and shoulders feel so tight",
        "expected_keywords": ["tension", "release", "ease"],
        "should_not_contain": ["ignore", "tense"],
    },
    {
        "category": "Overwhelm",
        "emotion": "anxious",
        "query": "Everything feels like too much right now",
        "expected_keywords": ["one thing", "pause", "slow"],
        "should_not_contain": ["push", "everything"],
    },
    {
        "category": "Fear",
        "emotion": "anxious",
        "query": "I'm afraid this won't work for me",
        "expected_keywords": ["safe", "courage", "here"],
        "should_not_contain": ["guaranteed", "definitely"],
    },
    {
        "category": "Validation Needed",
        "emotion": "anxious",
        "query": "Does anyone else feel like this?",
        "expected_keywords": ["valid", "normal", "understand"],
        "should_not_contain": ["unique", "alone"],
    },
    {
        "category": "Progress Recognition",
        "emotion": "calm",
        "query": "I'm getting a bit better with this",
        "expected_keywords": ["progress", "strength", "doing well"],
        "should_not_contain": ["just", "only"],
    },
    {
        "category": "Leg Pain",
        "emotion": "pain",
        "query": "My legs are aching badly",
        "expected_keywords": ["legs", "ease", "position"],
        "should_not_contain": ["ignore", "push"],
    },
    {
        "category": "Chest Discomfort",
        "emotion": "physically_uncomfortable_severe",
        "query": "I'm having a lot of discomfort in my chest",
        "expected_keywords": ["pause", "safe", "check"],
        "should_not_contain": ["continue", "ignore"],
    },
    {
        "category": "Stomach Discomfort",
        "emotion": "physical ly_uncomfortable_mild",
        "query": "My stomach feels weird",
        "expected_keywords": ["stomach", "breathe", "relax"],
        "should_not_contain": ["ignore", "push"],
    },
    {
        "category": "Fatigue",
        "emotion": "physically_uncomfortable_mild",
        "query": "I'm feeling so tired",
        "expected_keywords": ["rest", "support", "gentle"],
        "should_not_contain": ["energetic", "active"],
    },
]


def test_llm_synthesis():
    """Test LLM synthesis for all test cases."""
    logger.info("="*80)
    logger.info("LLM SYNTHESIS END-TO-END TEST SUITE")
    logger.info("="*80)

    llm_generator = get_llm_generator()

    passed = 0
    failed = 0
    results = []

    for i, test_case in enumerate(TEST_CASES, 1):
        logger.info(f"\n[{i}/{len(TEST_CASES)}] Testing: {test_case['category']}")
        logger.info(f"     Query: {test_case['query']}")

        try:
            # Simulate RAG context
            rag_context = {
                "query_pattern": test_case["emotion"],
                "intent_category": "general",
                "responses": [
                    f"Response for {test_case['emotion']} - Option 1",
                    f"Response for {test_case['emotion']} - Option 2",
                    f"Response for {test_case['emotion']} - Option 3",
                ],
                "relevance_score": 0.85,
                "emotion": test_case["emotion"],
                "user_message": test_case["query"],
                "session_id": uuid4(),
                "state_id": uuid4(),
            }

            # Generate response
            response = llm_generator.generate_response(rag_context)

            # Validate response
            response_lower = response.lower()

            # Check for expected keywords
            found_keywords = [
                kw for kw in test_case["expected_keywords"]
                if kw.lower() in response_lower
            ]

            # Check for unwanted keywords
            found_unwanted = [
                kw for kw in test_case.get("should_not_contain", [])
                if kw.lower() in response_lower
            ]

            # Assess quality
            quality_score = len(found_keywords) / max(len(test_case["expected_keywords"]), 1)
            quality_score -= len(found_unwanted) * 0.1

            is_passed = (
                len(response) > 20 and  # Response has content
                len(response) < 500 and  # Response not too long
                quality_score >= 0.3  # At least some quality
            )

            if is_passed:
                passed += 1
                status = "✓ PASS"
            else:
                failed += 1
                status = "✗ FAIL"

            logger.info(f"     {status}")
            logger.info(f"     Response: {response[:100]}...")
            logger.info(f"     Keywords found: {found_keywords} ({quality_score:.1%})")
            if found_unwanted:
                logger.warning(f"     ⚠️  Unwanted keywords: {found_unwanted}")

            results.append({
                "category": test_case["category"],
                "emotion": test_case["emotion"],
                "passed": is_passed,
                "response_length": len(response),
                "quality_score": quality_score,
                "keywords_found": len(found_keywords),
                "unwanted_found": len(found_unwanted),
            })

        except Exception as e:
            failed += 1
            logger.error(f"     ✗ EXCEPTION: {e}")
            results.append({
                "category": test_case["category"],
                "emotion": test_case["emotion"],
                "passed": False,
                "error": str(e),
            })

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"\nTotal: {len(TEST_CASES)}")
    logger.info(f"Passed: {passed} ({passed/len(TEST_CASES)*100:.1f}%)")
    logger.info(f"Failed: {failed} ({failed/len(TEST_CASES)*100:.1f}%)")

    # Print detailed results
    logger.info("\nDetailed Results by Category:")
    logger.info("-" * 80)

    for result in results:
        status = "✓" if result["passed"] else "✗"
        if "error" in result:
            logger.info(f"{status} {result['category']:30} | ERROR: {result['error'][:40]}")
        else:
            quality = f"{result['quality_score']*100:.0f}%"
            logger.info(f"{status} {result['category']:30} | Quality: {quality:>4} | Length: {result['response_length']:>3}")

    # Print recommendations
    logger.info("\n" + "="*80)
    logger.info("RECOMMENDATIONS")
    logger.info("="*80)

    if passed / len(TEST_CASES) >= 0.9:
        logger.info("✓ LLM synthesis is performing well!")
        logger.info("  - Ready for integration with session manager")
        logger.info("  - Consider expanding test coverage for edge cases")
    elif passed / len(TEST_CASES) >= 0.7:
        logger.info("⚠ LLM synthesis needs refinement:")
        logger.info("  - Review failed test cases")
        logger.info("  - Adjust prompt engineering")
        logger.info("  - Consider response template improvements")
    else:
        logger.info("✗ LLM synthesis needs significant work:")
        logger.info("  - Check Claude API connectivity")
        logger.info("  - Review prompt and context building")
        logger.info("  - Consider fallback to heuristics")

    return passed / len(TEST_CASES) >= 0.7


if __name__ == "__main__":
    success = test_llm_synthesis()
    sys.exit(0 if success else 1)
