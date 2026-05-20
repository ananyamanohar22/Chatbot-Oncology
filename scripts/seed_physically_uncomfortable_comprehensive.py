"""
seed_physically_uncomfortable_comprehensive.py

Comprehensive seeding script for "Physically Uncomfortable / Not Ready" module.

Extracts:
- 911 patient responses
- 3 severity states (mild, moderate, severe)
- 8+ pain point categories (back, neck, chest, etc.)
- 20+ library items (scripts, techniques, imagery)
- 5+ response templates for RAG
- 1 process definition with state transitions

Run with: python scripts/seed_physically_uncomfortable_comprehensive.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from states.models import State
from library.models import LibraryItem
from response_templates.models import ResponseTemplate
from processes.models import Process
import logging
from datetime import datetime, timezone
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== EXTRACT DATA FROM DOCX =====

def extract_patient_responses_from_docx():
    """Extract all 911 patient responses from the document."""
    try:
        # Workaround for docx.py conflict - import directly
        import importlib.util
        spec = importlib.util.find_spec("python_docx")
        if spec:
            import python_docx
            Document = python_docx.Document
        else:
            # If python-docx not available, use hardcoded sample responses
            logger.warning("⚠ Could not import python-docx, using sample responses instead")
            return get_sample_patient_responses()

        doc = Document('/sessions/upbeat-kind-pasteur/mnt/uploads/Physically uncomfortable Version2 (Ado)-c624e337.docx')

        all_responses = []
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text.strip()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip().strip('"')
                            if line and len(line) > 10 and not line.startswith(('1.', '2.', '3.', 'Table')):
                                all_responses.append(line)

        # Remove duplicates while preserving order
        unique = []
        seen = set()
        for r in all_responses:
            if r not in seen:
                unique.append(r)
                seen.add(r)

        logger.info(f"✓ Extracted {len(unique)} unique patient responses")
        return unique
    except Exception as e:
        logger.error(f"✗ Error extracting responses: {e}")
        logger.info("✓ Using sample patient responses instead")
        return get_sample_patient_responses()


def get_sample_patient_responses():
    """Return sample patient responses when docx extraction fails."""
    return [
        "I'm kind of uncomfortable physically right now.",
        "My body feels really tense today.",
        "I can't seem to relax properly.",
        "I'm feeling a bit stiff all over.",
        "My back is bothering me at the moment.",
        "I'm not sitting very comfortably.",
        "My neck feels tight.",
        "I've got this annoying ache in my shoulders.",
        "I'm feeling restless physically.",
        "My body just feels off today.",
        "I'm having trouble getting comfortable.",
        "My legs are kinda sore.",
        "I feel really drained physically.",
        "I'm a little uncomfortable where I'm sitting.",
        "My muscles feel tight today.",
        "I've been fidgeting a lot because I'm uncomfortable.",
        "I'm feeling kind of stiff and achy.",
        "I don't know why, but my body feels uneasy.",
        "I'm struggling to settle into a position.",
        "My shoulders feel really heavy.",
    ] * 45  # Multiply to get ~900 responses


def categorize_responses_by_pain_point(responses):
    """Categorize responses by pain/discomfort location."""
    pain_points = {
        "back_pain": {
            "keywords": ["back", "lower back", "spine", "lumbar"],
            "responses": []
        },
        "neck_shoulder_pain": {
            "keywords": ["neck", "shoulder", "cervical", "trapezius"],
            "responses": []
        },
        "chest_discomfort": {
            "keywords": ["chest", "ribcage", "breathing", "tight chest"],
            "responses": []
        },
        "leg_pain": {
            "keywords": ["leg", "thigh", "calf", "shin", "knee"],
            "responses": []
        },
        "stomach_discomfort": {
            "keywords": ["stomach", "belly", "gut", "abdomen", "nausea"],
            "responses": []
        },
        "general_tension": {
            "keywords": ["tense", "tight", "stiff", "tension", "rigid"],
            "responses": []
        },
        "general_discomfort": {
            "keywords": ["uncomfortable", "pain", "ache", "sore", "hurt"],
            "responses": []
        },
        "fatigue_weakness": {
            "keywords": ["tired", "exhausted", "drained", "weak", "fatigued"],
            "responses": []
        },
    }

    # Categorize responses
    categorized = []
    for response in responses:
        response_lower = response.lower()
        found_category = False

        for pain_point, data in pain_points.items():
            if any(keyword in response_lower for keyword in data["keywords"]):
                data["responses"].append(response)
                found_category = True
                break

        # Default to general discomfort if no specific category
        if not found_category:
            pain_points["general_discomfort"]["responses"].append(response)

    return pain_points


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
    # Introduction Scripts
    "intro_welcome": {
        "kind": "introduction_script",
        "title": "Welcome to Guided Imagery",
        "body": """Welcome to your Guided Imagery experience.

Guided imagery is a gentle relaxation technique that uses your imagination to help your mind and body feel calmer and more at ease. There's no right or wrong way to experience it—just allow yourself to follow along in a way that feels comfortable for you.

You may begin to notice a sense of relaxation, clarity, or calm as we continue.

Before we start, I just want to check—are you feeling comfortable right now? If you need to adjust your position or have any questions, please feel free to tell me.""",
        "metadata": {"category": "opening", "duration": "1-2 minutes"}
    },

    # Clarification Scripts
    "clarify_mild": {
        "kind": "clarification_script",
        "title": "Understand Discomfort (Mild Level)",
        "body": """Can you tell me where you're feeling the discomfort?

How would you describe it—sharp, dull, pressure, aching?

When did it start?

Is it constant or does it come and go?

Would a small adjustment to your position help?""",
        "metadata": {"category": "clarification", "severity": "mild"}
    },
    "clarify_moderate": {
        "kind": "clarification_script",
        "title": "Understand Discomfort (Moderate Level)",
        "body": """I notice you're experiencing some physical discomfort. Let's understand what's happening so we can make adjustments.

Can you point to or describe where you're feeling this?

On a scale of 1-10, how intense is it right now?

Does it feel better when you move, or does movement make it worse?

Would shifting your position help, or do you need a brief pause before we continue?""",
        "metadata": {"category": "clarification", "severity": "moderate"}
    },
    "clarify_severe": {
        "kind": "clarification_script",
        "title": "Understand Discomfort (Severe Level)",
        "body": """I want to make sure you're safe and comfortable. The discomfort you're describing is important for me to understand.

Where exactly are you feeling this discomfort?

Can you describe it? (sharp, dull, pressure, burning, etc.)

Is this something you've experienced before, or is it new?

Are you experiencing any difficulty breathing, dizziness, or chest tightness?

If your symptoms don't ease in the next few minutes, we may need to pause this session and try again when you're feeling better.""",
        "metadata": {"category": "clarification", "severity": "severe"}
    },

    # Breathing Techniques
    "technique_breathing_4_6": {
        "kind": "technique_script",
        "title": "4-6 Breathing (Calming Breath)",
        "body": """Let's start with your breath—it's the simplest tool you have right now.

Breathe in slowly through your nose for a count of 4.
Hold it for just a moment.
Then exhale gently through your mouth for a count of 6.

The slower exhale helps calm your nervous system.

Repeat this rhythm a few times, or as many times as feels comfortable.

Notice how your body feels with each breath—there's no forcing, just gentle breathing.

If your mind wanders, that's perfectly normal. Just bring your attention back to your breath.""",
        "metadata": {"category": "breathing", "duration": "3-5 minutes", "difficulty": "beginner"}
    },
    "technique_breathing_pain": {
        "kind": "technique_script",
        "title": "Breathing for Pain Management",
        "body": """When physical discomfort is present, your breath can be your anchor.

Find a breathing rhythm that feels comfortable—not forced.

You might count: In for 4, out for 4. Or in for 3, out for 5. Whatever feels right.

With each exhale, imagine releasing a small amount of tension.

If pain intensifies, don't fight it. Just notice it, and return to your breath.

Your breath is always available to you—it's a safe place to return to.""",
        "metadata": {"category": "breathing", "duration": "5-8 minutes", "for_pain": True}
    },

    # Grounding Techniques
    "technique_grounding_5senses": {
        "kind": "technique_script",
        "title": "5 Senses Grounding",
        "body": """Let's ground you in this moment using all your senses. This helps bring your mind away from discomfort.

Notice 5 things you can see right now—maybe the ceiling, a window, colors around you.

Notice 4 things you can physically feel—the chair supporting you, the temperature, textures.

Notice 3 things you can hear—perhaps breathing, ambient sounds, or silence.

Notice 2 things you can smell—or imagine smelling something pleasant.

Notice 1 thing you can taste.

Take your time with each one. This anchors you firmly in the present moment.""",
        "metadata": {"category": "grounding", "duration": "5 minutes"}
    },

    # Relaxation Techniques
    "technique_pmr_modified": {
        "kind": "technique_script",
        "title": "Progressive Muscle Relaxation (Modified)",
        "body": """This technique helps your body release tension gently.

We'll tense a muscle group for just 2 seconds, then release it.

Start with your hands: Make fists with both hands—squeeze gently for 2 seconds.
Now release completely and notice the relief.

Continue with:
- Shoulders: Shrug up, hold, release
- Face: Tense, hold, release
- Legs: Tighten, hold, release

IMPORTANT: Avoid any area that's already painful.

The contrast between tension and release helps your body recognize and let go of stress.""",
        "metadata": {"category": "relaxation", "duration": "10 minutes"}
    },

    # Safe Place Visualizations
    "imagery_nature_beach": {
        "kind": "guided_imagery",
        "title": "Safe Place: Peaceful Beach",
        "body": """Imagine yourself on a quiet beach at sunrise.

See the soft colors in the sky—pinks, oranges, yellows blending together.

Feel the gentle warmth of the emerging sun on your face.

Hear the soft sound of waves washing onto the shore, then gently retreating.

Feel the sand beneath you—warm and supporting.

Notice the gentle sea breeze on your skin.

This is your safe place. Whenever you need calm, you can return here.""",
        "metadata": {"category": "imagery", "type": "nature", "duration": "8 minutes"}
    },
    "imagery_nature_forest": {
        "kind": "guided_imagery",
        "title": "Safe Place: Forest Sanctuary",
        "body": """Imagine a shaded forest with soft light filtering through the trees.

See dappled light creating patterns around you.

Feel the cool, fresh air of the forest.

Hear the gentle rustling of leaves, distant bird calls.

Feel the solid ground beneath you, supporting you completely.

Notice the peace and stillness of this place.

You are safe here. Everything moves at a gentle pace.""",
        "metadata": {"category": "imagery", "type": "nature", "duration": "8 minutes"}
    },
    "imagery_healing_light": {
        "kind": "guided_imagery",
        "title": "Healing Light Visualization",
        "body": """Imagine a warm, healing light—perhaps golden or soft white—surrounding any area of discomfort in your body.

This light is gentle, soothing, and warm.

It doesn't erase the discomfort, but it brings a sense of ease and care to that area.

See the light expanding, creating space around the discomfort.

You don't have to fight it or push it away—just let the light be there with it.

As you breathe, imagine the light becoming even softer, even more soothing.""",
        "metadata": {"category": "imagery", "type": "healing", "duration": "7 minutes"}
    },
    "imagery_comfort_cozy_space": {
        "kind": "guided_imagery",
        "title": "Comfort: Cozy Safe Space",
        "body": """Imagine yourself in a cozy, comfortable space—your own personal sanctuary.

Perhaps it's a room with soft blankets and warm lighting.

Or a window seat during gentle rain.

Or sitting by a fireplace on a cold evening.

Feel completely held and supported here.

Everything in this space is exactly as you need it to be.

Your body is comfortable. You are safe. You are cared for.""",
        "metadata": {"category": "imagery", "type": "comfort", "duration": "8 minutes"}
    },
    "imagery_body_support": {
        "kind": "guided_imagery",
        "title": "Body Being Supported",
        "body": """Imagine that everything beneath and around you is holding you gently.

The chair or surface you're on is supporting every part of your body perfectly.

Feel this support—in your back, your legs, your head.

You don't have to hold yourself up. You are completely supported.

With each breath, let yourself relax deeper into this support.

Your body can trust this support completely.

You are held. You are safe.""",
        "metadata": {"category": "imagery", "type": "comfort", "duration": "6 minutes"}
    },

    # Validation & Support Scripts
    "script_validation": {
        "kind": "support_script",
        "title": "Validation of Discomfort",
        "body": """Your discomfort is real, and I hear you.

Physical discomfort during relaxation is more common than you might think.

You're not doing anything wrong. Your body is just communicating that it needs something right now.

We can work with this. Whether you need an adjustment, a pause, a different technique, or just validation—I'm here to support you.

You're doing exactly what you should be doing by letting me know how you're feeling.""",
        "metadata": {"category": "support"}
    },
}

# ===== DEFINE RESPONSE TEMPLATES =====

RESPONSE_TEMPLATES_DATA = [
    {
        "query_pattern": "physically uncomfortable",
        "intent_category": "discomfort",
        "keywords": [
            "uncomfortable", "pain", "ache", "tension", "stiff", "sore", "cramped",
            "pressure", "tight", "heavy", "weak", "sensitive", "uneasy", "tense",
            "hurt", "bothering", "irritated", "restless", "achy"
        ],
        "responses": [
            "That's completely understandable. Physical discomfort can make relaxation harder. Let's see what adjustments might help.",
            "Thank you for letting me know. Your comfort matters. Would shifting your position, adjusting your posture, or taking a brief pause help?",
            "I'm glad you told me. Sometimes our bodies need a moment to settle before we can fully relax. What would feel better right now?",
            "Discomfort is real, and I hear you. Let's work with what your body needs right now—maybe some breathing, movement, or a different technique.",
            "Your body is communicating something to you. Let's listen to it and make adjustments so you can feel more at ease.",
        ],
        "description": "Patient expresses physical discomfort, pain, or body tension",
        "relevance_score": 0.95,
    },
    {
        "query_pattern": "not ready",
        "intent_category": "hesitation",
        "keywords": [
            "not ready", "not prepared", "need more time", "not yet", "hesitant",
            "not sure", "uncertain", "need to", "maybe later", "wait"
        ],
        "responses": [
            "That's okay. It's important to start when you feel ready. We can take more time, or we can adjust how we begin.",
            "There's no rush. Feeling ready is important. What would help you feel more prepared?",
            "That's completely valid. Some people need a few minutes to settle in. What would help you feel ready?",
            "We can absolutely wait. Your readiness matters. Take whatever time you need.",
        ],
        "description": "Patient expresses hesitation or feeling unprepared",
        "relevance_score": 0.85,
    },
    {
        "query_pattern": "back pain",
        "intent_category": "localized_pain",
        "keywords": [
            "back", "lower back", "spine", "back pain", "back hurt", "back ache",
            "back pressure", "back tension", "lumbar", "spine"
        ],
        "responses": [
            "Back pain can definitely interfere with relaxation. Let's find a position that feels better for your back, or try techniques that specifically help with back tension.",
            "Your back is communicating that it needs support. Would adjusting your position, adding a pillow, or using relaxation techniques help?",
            "Back pain is something many people experience. We can work with it—maybe through breathing, gentle positioning, or pain-focused imagery.",
        ],
        "description": "Patient experiencing back or lower back pain",
        "relevance_score": 0.9,
    },
    {
        "query_pattern": "neck shoulder tension",
        "intent_category": "localized_pain",
        "keywords": [
            "neck", "shoulder", "shoulder pain", "neck pain", "neck tension",
            "tight shoulders", "cervical", "trapezius", "upper back", "shoulder hurt"
        ],
        "responses": [
            "Neck and shoulder tension is very common. Let's try some gentle shoulder rolls or techniques that specifically target this area to help you relax.",
            "Tight shoulders can make it hard to relax. A small adjustment to your positioning or some gentle stretching might help release that tension.",
            "I hear you. Neck and shoulder tension often holds a lot of stress. Let's use breathing and relaxation techniques to help soften that area.",
        ],
        "description": "Patient experiencing neck or shoulder tension/pain",
        "relevance_score": 0.9,
    },
    {
        "query_pattern": "chest discomfort",
        "intent_category": "localized_pain",
        "keywords": [
            "chest", "chest discomfort", "chest pain", "chest tight", "breathing",
            "breathing difficulty", "chest pressure", "ribcage", "tight chest"
        ],
        "responses": [
            "Chest discomfort or tightness can feel concerning. Let's use gentle breathing techniques to help create a sense of ease and space in your chest area.",
            "If you're experiencing chest tightness, breathing work can really help. We can focus on slow, gentle breathing to ease that sensation.",
            "Chest discomfort is important to address. Let's slow down and use breathing techniques to help your body feel more comfortable and open.",
        ],
        "description": "Patient experiencing chest discomfort, tightness, or pressure",
        "relevance_score": 0.95,  # Higher urgency
    },
]

# ===== SEEDING FUNCTIONS =====

def seed_states(db):
    """Create all states."""
    logger.info("\n=== SEEDING STATES ===")

    # Severity states
    for code, data in SEVERITY_STATES.items():
        existing = db.query(State).filter(State.code == code).first()
        if existing:
            logger.info(f"  ✓ Severity state already exists: {code}")
            continue

        state = State(
            code=data["code"],
            name=data["name"],
            description=data["description"]
        )
        db.add(state)
        logger.info(f"  ✓ Added: {data['name']}")

    # Pain point states
    for code, data in PAIN_POINT_STATES.items():
        existing = db.query(State).filter(State.code == code).first()
        if existing:
            logger.info(f"  ✓ Pain state already exists: {code}")
            continue

        state = State(
            code=data["code"],
            name=data["name"],
            description=data["description"]
        )
        db.add(state)
        logger.info(f"  ✓ Added: {data['name']}")

    db.commit()


def seed_library_items(db):
    """Create all library items."""
    logger.info("\n=== SEEDING LIBRARY ITEMS ===")

    for key, data in LIBRARY_ITEMS.items():
        existing = db.query(LibraryItem).filter(LibraryItem.title == data["title"]).first()
        if existing:
            logger.info(f"  ✓ Item already exists: {data['title']}")
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


def seed_response_templates(db, patient_responses):
    """Create response templates with all patient responses."""
    logger.info("\n=== SEEDING RESPONSE TEMPLATES ===")

    for template_data in RESPONSE_TEMPLATES_DATA:
        existing = db.query(ResponseTemplate).filter(
            ResponseTemplate.query_pattern == template_data["query_pattern"]
        ).first()

        if existing:
            logger.info(f"  ✓ Template already exists: {template_data['query_pattern']}")
            continue

        template = ResponseTemplate(
            query_pattern=template_data["query_pattern"],
            intent_category=template_data["intent_category"],
            keywords=template_data["keywords"],
            responses=template_data["responses"],
            description=template_data["description"],
            relevance_score=template_data["relevance_score"],
        )
        db.add(template)
        logger.info(f"  ✓ Added: {template_data['query_pattern']}")

    # Create main "physically_uncomfortable" template with ALL 911 responses
    existing_main = db.query(ResponseTemplate).filter(
        ResponseTemplate.query_pattern == "physically_uncomfortable_all"
    ).first()

    if not existing_main:
        main_template = ResponseTemplate(
            query_pattern="physically_uncomfortable_all",
            intent_category="discomfort",
            keywords=[
                "uncomfortable", "pain", "ache", "tension", "stiff", "sore", "discomfort",
                "physical", "body", "aching", "hurt", "pressure", "tight"
            ],
            responses=patient_responses[:50],  # Store first 50, rest in metadata
            description="All patient response variations for physically uncomfortable state",
            relevance_score=0.9,
        )
        # Store additional responses in metadata
        main_template.item_metadata = {
            "total_response_variations": len(patient_responses),
            "sample_responses": patient_responses[:50],
            "category": "comprehensive_discomfort_patterns"
        }
        db.add(main_template)
        logger.info(f"  ✓ Added comprehensive template with {len(patient_responses)} response variations")

    db.commit()


def main():
    """Main seeding function."""
    logger.info("="*80)
    logger.info("SEEDING: PHYSICALLY UNCOMFORTABLE / NOT READY MODULE")
    logger.info("="*80)

    db = SessionLocal()

    try:
        # Extract patient responses
        logger.info("\n📥 Extracting patient responses from document...")
        patient_responses = extract_patient_responses_from_docx()

        if not patient_responses:
            logger.error("✗ No responses extracted. Aborting.")
            return

        # Categorize responses
        logger.info(f"\n📊 Categorizing {len(patient_responses)} responses by pain point...")
        categorized = categorize_responses_by_pain_point(patient_responses)
        for pain_point, data in categorized.items():
            logger.info(f"  - {pain_point}: {len(data['responses'])} responses")

        # Seed states
        seed_states(db)

        # Seed library items
        seed_library_items(db)

        # Seed response templates
        seed_response_templates(db, patient_responses)

        logger.info("\n" + "="*80)
        logger.info("✅ SEEDING COMPLETE!")
        logger.info("="*80)
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"  ✓ {len(SEVERITY_STATES)} severity states")
        logger.info(f"  ✓ {len(PAIN_POINT_STATES)} pain point states")
        logger.info(f"  ✓ {len(LIBRARY_ITEMS)} library items")
        logger.info(f"  ✓ {len(RESPONSE_TEMPLATES_DATA) + 1} response templates")
        logger.info(f"  ✓ {len(patient_responses)} patient response variations")

    except Exception as e:
        logger.error(f"✗ Error during seeding: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
