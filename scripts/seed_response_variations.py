"""
seed_response_variations.py

Seed comprehensive response variations for different emotions and scenarios.
This provides rich options for LLM synthesis to choose from.

Response categories:
- Physical discomfort (mild, moderate, severe)
- Anxiety/fear
- Hesitation/not ready
- Pain validation
- Breathing support
- Grounding support
- Guided imagery support
- Progress acknowledgment
- Encouragement
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from response_templates.models import ResponseTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define comprehensive response variations
RESPONSE_VARIATIONS = {
    "physically_uncomfortable_mild": {
        "intent_category": "discomfort",
        "keywords": ["uncomfortable", "slight", "minor", "little", "bit", "mild"],
        "responses": [
            "I hear you. Small adjustments can often make a big difference. What position would feel most comfortable for you right now?",
            "Thank you for letting me know. Let's work with what your body needs. Would a small repositioning help?",
            "That's helpful information. Even minor discomfort is worth addressing. How can we make you more comfortable?",
            "I appreciate you sharing that. Let's find small ways to ease how you're feeling.",
            "You're doing well to notice that. Sometimes gentle adjustments are all we need. What would help most?",
        ],
        "relevance_score": 0.95,
    },

    "physically_uncomfortable_moderate": {
        "intent_category": "discomfort",
        "keywords": ["uncomfortable", "moderate", "quite", "pretty", "significant", "noticeable"],
        "responses": [
            "I understand. Moderate discomfort definitely deserves our attention. Let's pause and make some adjustments before we continue.",
            "Thank you for being honest about what you're experiencing. We can take time to address this. What would help ease your discomfort?",
            "That's important information. Let's work together to make you more comfortable. Would you like to try repositioning or take a brief break?",
            "I hear you. When discomfort is noticeable, it's worth taking action. Let's find what works best for your body right now.",
            "Your comfort is important. Let's explore what adjustments might help you feel better before we continue.",
        ],
        "relevance_score": 0.92,
    },

    "physically_uncomfortable_severe": {
        "intent_category": "discomfort",
        "keywords": ["severely", "very badly", "intense", "significant", "can't", "unable", "struggling"],
        "responses": [
            "I can hear that you're experiencing significant discomfort. Your safety and comfort come first. Let's pause and address this.",
            "That sounds really uncomfortable. I want to make sure you're okay. Would it help to adjust your position, take a break, or check in with medical support?",
            "I'm glad you're telling me. Intense discomfort is important. Let's stop and focus on what you need right now.",
            "Your experience matters. When discomfort is this significant, we should pause and make sure you have what you need.",
            "I hear the intensity in what you're describing. Let's take a moment and focus on making you more comfortable. What would help most?",
        ],
        "relevance_score": 0.96,
    },

    "anxiety": {
        "intent_category": "anxiety",
        "keywords": ["anxious", "nervous", "worried", "scared", "afraid", "panic", "overwhelming"],
        "responses": [
            "It's completely normal to feel anxious. You're safe, and I'm here with you. Let's take this one moment at a time.",
            "Anxiety is your mind trying to protect you. That's actually wise. Let's work together to help you feel safer and calmer.",
            "What you're feeling is valid. Many people feel this way. Let's focus on your breath and what you can control right now.",
            "Your feelings matter. Anxiety often lessens when we pause and ground ourselves in the present moment.",
            "I understand. Feeling anxious is a sign you care about what's happening. Let's use some techniques to help you settle.",
        ],
        "relevance_score": 0.90,
    },

    "hesitation_not_ready": {
        "intent_category": "hesitation",
        "keywords": ["not ready", "hesitant", "unsure", "not sure", "don't know", "need time"],
        "responses": [
            "That's completely okay. There's no rush. We can move at whatever pace feels right for you.",
            "Your hesitation is important. It tells us we should take our time. What would help you feel more ready?",
            "It's perfectly fine to feel unsure. Taking time to prepare is actually a strength. What do you need?",
            "I appreciate your honesty. Readiness is important. We have all the time you need.",
            "Not feeling ready is valid. Let's talk about what would help you feel more comfortable moving forward.",
        ],
        "relevance_score": 0.88,
    },

    "validation_acknowledgment": {
        "intent_category": "validation",
        "keywords": ["real", "valid", "understand", "hear", "acknowledge"],
        "responses": [
            "What you're experiencing is completely real and valid. Your feelings matter.",
            "I hear you, and I understand. Your experience is important.",
            "That's real, and it's understandable that you feel this way. You're not alone in this.",
            "Your feelings make sense given what you're going through. They're completely valid.",
            "I acknowledge what you're experiencing. It's genuine, and it's okay to feel this way.",
        ],
        "relevance_score": 0.92,
    },

    "breathing_support": {
        "intent_category": "technique",
        "keywords": ["breathing", "breath", "breathe", "calm", "settle"],
        "responses": [
            "Let's focus on your breath for a moment. Breathing is one of your body's natural tools for calming itself.",
            "Your breath can be a powerful anchor. Let's try a gentle breathing rhythm together.",
            "When things feel overwhelming, your breath can help settle your nervous system. Let's try a simple technique.",
            "Would you like to try a calming breathing practice? It's a gentle way to help your body relax.",
            "Focusing on your breath can create a sense of calm. Let's try breathing in slowly and exhaling even more slowly.",
        ],
        "relevance_score": 0.89,
    },

    "grounding_support": {
        "intent_category": "technique",
        "keywords": ["grounding", "present", "here", "now", "senses", "anchor"],
        "responses": [
            "Let's ground you in the present moment using your five senses. This can help you feel more anchored and calm.",
            "Grounding helps bring your mind back to the here and now. Let's notice what you can see, hear, and feel around you.",
            "When the mind wanders to worry, we can bring it back to the present through our senses.",
            "Grounding is a simple but powerful way to steady yourself. Would you like to try it with me?",
            "Let's connect with the present moment. Notice your body, the space around you, what you can sense right now.",
        ],
        "relevance_score": 0.87,
    },

    "imagery_support": {
        "intent_category": "technique",
        "keywords": ["imagine", "imagine", "visualization", "visualization", "safe place", "peaceful"],
        "responses": [
            "Your imagination is a powerful tool for healing. Let's explore a peaceful place in your mind.",
            "Guided imagery can help your mind and body relax deeply. Would you like to visualize a place that feels safe?",
            "Close your eyes and let's journey to a place of calm and safety that you create in your mind.",
            "Visualization is a gentle way to shift how you feel. Let's imagine something peaceful together.",
            "Your mind has the ability to create experiences of calm. Let's use that power together.",
        ],
        "relevance_score": 0.86,
    },

    "progress_acknowledgment": {
        "intent_category": "encouragement",
        "keywords": ["progress", "doing well", "strength", "courage", "brave"],
        "responses": [
            "You're doing really well. The fact that you're here and engaging shows real strength.",
            "I'm noticing your progress. You're showing up for yourself, and that matters.",
            "Look at what you're already doing. You're taking care of yourself in a meaningful way.",
            "Your commitment to this process is clear. That takes real courage.",
            "You're making genuine progress. Notice what you're learning about yourself and what helps.",
        ],
        "relevance_score": 0.91,
    },

    "encouragement": {
        "intent_category": "encouragement",
        "keywords": ["encourage", "continue", "keep going", "you can", "possible"],
        "responses": [
            "You're capable of more than you know. Let's discover that together.",
            "Every step you take matters. Keep moving forward at your own pace.",
            "You have the resources you need within you. Let's access them together.",
            "This is working. I can see your commitment, and it's creating change.",
            "You're building new skills and awareness. That's something to be proud of.",
        ],
        "relevance_score": 0.85,
    },

    "pain_location_back": {
        "intent_category": "pain",
        "keywords": ["back", "lower back", "spine", "back pain"],
        "responses": [
            "Back pain is common but definitely something we can address. Let's explore what helps.",
            "I understand back pain can really limit what feels possible. Let's find positions and techniques that help ease it.",
            "Your back is important to your comfort. We can work with gentle techniques to ease this.",
            "Back discomfort often responds well to subtle adjustments and gentle support. Let's try that.",
            "That area holds a lot of tension for many people. We have good options to help ease it.",
        ],
        "relevance_score": 0.88,
    },

    "pain_location_neck_shoulder": {
        "intent_category": "pain",
        "keywords": ["neck", "shoulder", "tension", "tight", "upper back"],
        "responses": [
            "Neck and shoulder tension is really common. Gentle techniques work well for this area.",
            "That's an area where we hold a lot of stress. Let's work on easing that tension.",
            "Neck and shoulder discomfort often responds quickly to the right approach. We have good options.",
            "Tension in this area can affect how you feel overall. Let's release it together.",
            "That's a vulnerable area. We'll be gentle while we work to ease the tension you're experiencing.",
        ],
        "relevance_score": 0.87,
    },

    "pain_location_head": {
        "intent_category": "pain",
        "keywords": ["head", "headache", "migraine", "temples", "pressure"],
        "responses": [
            "Headaches can make everything feel harder. We have techniques that can help ease this.",
            "Tension headaches often respond well to relaxation and breathing work.",
            "Head pain is something we can address. Relaxation and gentle techniques often help significantly.",
            "Migraines and tension headaches have different needs. Let's explore what works for you.",
            "Easing head tension can help you feel more like yourself. Let's work on that.",
        ],
        "relevance_score": 0.86,
    },

    "pain_location_chest": {
        "intent_category": "pain",
        "keywords": ["chest", "chest pain", "chest tension", "tightness", "pressure"],
        "responses": [
            "Chest tension or discomfort deserves attention. Let's approach this carefully and supportively.",
            "Chest tightness often connects to how we breathe and carry stress. We can work with that.",
            "If you're experiencing chest symptoms, we want to make sure you're safe. Have you checked with a doctor about this?",
            "Chest discomfort can feel very real. Let's address it with breathing and gentle relaxation.",
            "Tightness in the chest often eases with the right approach to breathing and releasing tension.",
        ],
        "relevance_score": 0.89,
    },

    "fear_safety": {
        "intent_category": "fear",
        "keywords": ["afraid", "fear", "scared", "frightened", "safe"],
        "responses": [
            "Fear is trying to protect you. That's actually your wisdom. You're safe here with me.",
            "What you're afraid of makes sense. Let's work through it together at your pace.",
            "Fear often lessens when we face it gently, with support. I'm here with you.",
            "Your fear is valid. And you're here, you're safe, and we can work through this.",
            "Being afraid is human. Let's build your sense of safety and control step by step.",
        ],
        "relevance_score": 0.91,
    },

    "overwhelm": {
        "intent_category": "overwhelm",
        "keywords": ["overwhelmed", "overwhelm", "too much", "can't handle", "too hard"],
        "responses": [
            "When things feel overwhelming, remember: we don't have to solve everything at once.",
            "Overwhelm is a sign you need to slow down and focus on one thing at a time.",
            "You don't have to do this perfectly. Taking small steps is enough.",
            "When you're overwhelmed, simplicity is your friend. Let's focus on just what's essential.",
            "Feeling overwhelmed is actually feedback that you need support. That's okay. I'm here.",
        ],
        "relevance_score": 0.88,
    },
}


def main():
    """Main seeding function."""
    logger.info("="*80)
    logger.info("SEEDING: RESPONSE VARIATIONS FOR MULTIPLE EMOTIONS")
    logger.info("="*80)

    db = SessionLocal()

    try:
        logger.info(f"\n=== SEEDING {len(RESPONSE_VARIATIONS)} RESPONSE TEMPLATES ===")

        created_count = 0
        updated_count = 0

        for key, data in RESPONSE_VARIATIONS.items():
            # Check if template already exists
            existing = db.query(ResponseTemplate).filter(
                ResponseTemplate.query_pattern == key
            ).first()

            if existing:
                # Update if exists
                existing.responses = data["responses"]
                existing.relevance_score = data["relevance_score"]
                db.add(existing)
                updated_count += 1
                logger.info(f"  ✓ Updated: {key} ({len(data['responses'])} responses)")
            else:
                # Create new
                template = ResponseTemplate(
                    query_pattern=key,
                    intent_category=data["intent_category"],
                    description=f"Response variations for {key}",
                    responses=data["responses"],
                    keywords=data["keywords"],
                    relevance_score=data["relevance_score"],
                    is_active=True,
                )
                db.add(template)
                created_count += 1
                logger.info(f"  ✓ Created: {key} ({len(data['responses'])} responses)")

        db.commit()

        logger.info("\n" + "="*80)
        logger.info("✅ SEEDING COMPLETE!")
        logger.info("="*80)
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"  ✓ Created: {created_count} new templates")
        logger.info(f"  ✓ Updated: {updated_count} existing templates")
        logger.info(f"  ✓ Total response variations: {sum(len(d['responses']) for d in RESPONSE_VARIATIONS.values())}")
        logger.info(f"  ✓ Template coverage: {len(RESPONSE_VARIATIONS)} emotion/scenario categories")

    except Exception as e:
        logger.error(f"✗ Error during seeding: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
