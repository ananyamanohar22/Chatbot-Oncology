"""
seed_physically_uncomfortable_simple.py

Simple seeding without importing ResponseTemplate (to avoid cache issues).
Seeds states and library items only.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from states.models import State
from library.models import LibraryItem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== DEFINE STATES =====

SEVERITY_STATES = {
    "physically_uncomfortable_mild": {
        "code": "physically_uncomfortable_mild",
        "name": "Physically Uncomfortable (Mild)",
        "description": "Slight discomfort but patient can engage with support. Minor adjustments may help.",
    },
    "physically_uncomfortable_moderate": {
        "code": "physically_uncomfortable_moderate",
        "name": "Physically Uncomfortable (Moderate)",
        "description": "Moderate discomfort that may interfere with relaxation. Requires repositioning or brief intervention.",
    },
    "physically_uncomfortable_severe": {
        "code": "physically_uncomfortable_severe",
        "name": "Physically Uncomfortable (Severe)",
        "description": "Significant distress or concerning symptoms. May require pausing session or seeking medical assessment.",
    },
}

PAIN_POINT_STATES = {
    "pain_localized_back": {
        "code": "pain_localized_back",
        "name": "Localized Back Pain",
        "description": "Patient experiencing pain in back or lower back region",
    },
    "pain_neck_shoulder": {
        "code": "pain_neck_shoulder",
        "name": "Neck/Shoulder Tension",
        "description": "Patient experiencing tension or pain in neck, shoulders, or upper back",
    },
    "pain_chest": {
        "code": "pain_chest",
        "name": "Chest Discomfort",
        "description": "Patient experiencing chest tightness, pressure, or discomfort",
    },
    "pain_leg": {
        "code": "pain_leg",
        "name": "Leg Pain",
        "description": "Patient experiencing pain in legs, thighs, or lower extremities",
    },
    "pain_stomach": {
        "code": "pain_stomach",
        "name": "Stomach/Digestive Discomfort",
        "description": "Patient experiencing stomach upset, nausea, or digestive discomfort",
    },
    "general_tension": {
        "code": "general_tension",
        "name": "General Body Tension",
        "description": "Patient experiencing widespread tension or stiffness throughout body",
    },
    "fatigue_weakness": {
        "code": "fatigue_weakness",
        "name": "Fatigue/Weakness",
        "description": "Patient feeling tired, exhausted, or physically weak",
    },
}

# ===== DEFINE LIBRARY ITEMS =====

LIBRARY_ITEMS = {
    "intro_welcome": {
        "kind": "introduction_script",
        "title": "Welcome to Guided Imagery",
        "body": """Welcome to your Guided Imagery experience.

Guided imagery is a gentle relaxation technique that uses your imagination to help your mind and body feel calmer and more at ease.""",
        "metadata": {"category": "opening", "duration": "1-2 minutes"}
    },
    "clarify_mild": {
        "kind": "clarification_script",
        "title": "Understand Discomfort (Mild Level)",
        "body": """Can you tell me where you're feeling the discomfort? How would you describe it?""",
        "metadata": {"category": "clarification", "severity": "mild"}
    },
    "clarify_moderate": {
        "kind": "clarification_script",
        "title": "Understand Discomfort (Moderate Level)",
        "body": """I notice you're experiencing some physical discomfort. Let's understand what's happening so we can make adjustments.""",
        "metadata": {"category": "clarification", "severity": "moderate"}
    },
    "clarify_severe": {
        "kind": "clarification_script",
        "title": "Understand Discomfort (Severe Level)",
        "body": """I want to make sure you're safe and comfortable. The discomfort you're describing is important for me to understand.""",
        "metadata": {"category": "clarification", "severity": "severe"}
    },
    "technique_breathing_4_6": {
        "kind": "technique_script",
        "title": "4-6 Breathing (Calming Breath)",
        "body": """Let's start with your breath. Breathe in slowly through your nose for a count of 4. Then exhale gently for a count of 6. Repeat this rhythm.""",
        "metadata": {"category": "breathing", "duration": "3-5 minutes", "difficulty": "beginner"}
    },
    "technique_breathing_pain": {
        "kind": "technique_script",
        "title": "Breathing for Pain Management",
        "body": """When physical discomfort is present, your breath can be your anchor. Find a breathing rhythm that feels comfortable—not forced.""",
        "metadata": {"category": "breathing", "duration": "5-8 minutes", "for_pain": True}
    },
    "technique_grounding_5senses": {
        "kind": "technique_script",
        "title": "5 Senses Grounding",
        "body": """Let's ground you in this moment using all your senses. Notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.""",
        "metadata": {"category": "grounding", "duration": "5 minutes"}
    },
    "technique_pmr_modified": {
        "kind": "technique_script",
        "title": "Progressive Muscle Relaxation (Modified)",
        "body": """This technique helps your body release tension. We'll tense and release muscle groups. Avoid any area that's already painful.""",
        "metadata": {"category": "relaxation", "duration": "10 minutes"}
    },
    "imagery_nature_beach": {
        "kind": "guided_imagery",
        "title": "Safe Place: Peaceful Beach",
        "body": """Imagine yourself on a quiet beach at sunrise. Feel the gentle warmth of the emerging sun. Hear the soft sound of waves. This is your safe place.""",
        "metadata": {"category": "imagery", "type": "nature", "duration": "8 minutes"}
    },
    "imagery_healing_light": {
        "kind": "guided_imagery",
        "title": "Healing Light Visualization",
        "body": """Imagine a warm, healing light surrounding any area of discomfort. It brings ease and care. You don't have to fight it—just let the light be there with it.""",
        "metadata": {"category": "imagery", "type": "healing", "duration": "7 minutes"}
    },
    "script_validation": {
        "kind": "support_script",
        "title": "Validation of Discomfort",
        "body": """Your discomfort is real, and I hear you. You're not doing anything wrong. Let's work with what your body needs right now.""",
        "metadata": {"category": "support"}
    },
}


def main():
    """Main seeding function."""
    logger.info("="*80)
    logger.info("SEEDING: PHYSICALLY UNCOMFORTABLE / NOT READY MODULE")
    logger.info("="*80)

    db = SessionLocal()

    try:
        # Seed severity states
        logger.info("\n=== SEEDING SEVERITY STATES ===")
        for code, data in SEVERITY_STATES.items():
            existing = db.query(State).filter(State.code == code).first()
            if existing:
                logger.info(f"  ✓ Already exists: {code}")
                continue

            state = State(
                code=data["code"],
                name=data["name"],
                description=data["description"]
            )
            db.add(state)
            logger.info(f"  ✓ Added: {data['name']}")

        db.commit()

        # Seed pain point states
        logger.info("\n=== SEEDING PAIN POINT STATES ===")
        for code, data in PAIN_POINT_STATES.items():
            existing = db.query(State).filter(State.code == code).first()
            if existing:
                logger.info(f"  ✓ Already exists: {code}")
                continue

            state = State(
                code=data["code"],
                name=data["name"],
                description=data["description"]
            )
            db.add(state)
            logger.info(f"  ✓ Added: {data['name']}")

        db.commit()

        # Seed library items
        logger.info("\n=== SEEDING LIBRARY ITEMS ===")
        for key, data in LIBRARY_ITEMS.items():
            existing = db.query(LibraryItem).filter(LibraryItem.title == data["title"]).first()
            if existing:
                logger.info(f"  ✓ Already exists: {data['title']}")
                continue

            item = LibraryItem(
                kind=data["kind"],
                title=data["title"],
                body=data["body"],
                item_metadata=data["metadata"]
            )
            db.add(item)
            logger.info(f"  ✓ Added: {data['title']}")

        db.commit()

        logger.info("\n" + "="*80)
        logger.info("✅ SEEDING COMPLETE!")
        logger.info("="*80)
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"  ✓ {len(SEVERITY_STATES)} severity states")
        logger.info(f"  ✓ {len(PAIN_POINT_STATES)} pain point states")
        logger.info(f"  ✓ {len(LIBRARY_ITEMS)} library items")
        logger.info(f"\n✓ Next step: Add ResponseTemplates with 911 patient responses")

    except Exception as e:
        logger.error(f"✗ Error during seeding: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
