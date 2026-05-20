"""
scripts/seed_response_templates.py
Seed response templates into the database.

Run with: python scripts/seed_response_templates.py

This script adds common patient query patterns and their corresponding
response templates for RAG retrieval.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from response_templates.models import ResponseTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Template definitions: (pattern, category, keywords, responses, relevance_score)
TEMPLATES = [
    {
        "query_pattern": "not ready",
        "intent_category": "hesitation",
        "keywords": ["not ready", "im not ready", "not prepared", "not yet", "not now"],
        "responses": [
            "It's okay to not feel ready right now. Let's take a small 10-second break and just breathe together.",
            "This is a safe space where there's no judgment. Take your time. Let's do a few deep breaths when you're ready.",
            "I hear you. Is there anything I can do to help, or would it help to talk about what's making you uncomfortable?",
            "That's completely normal. Some people need a moment before starting. We can go at whatever pace feels right for you.",
        ],
        "description": "Patient expresses hesitation or feeling unprepared",
        "relevance_score": 0.9,
    },
    {
        "query_pattern": "afraid",
        "intent_category": "fear",
        "keywords": ["afraid", "scared", "fear", "anxious", "nervous", "worried"],
        "responses": [
            "It's natural to feel nervous about this. Remember, you're in complete control. We can take this as slowly as you need.",
            "What you're feeling is valid. Let's focus on your breathing first—slow, gentle breaths can help calm your nervous system.",
            "I'm here with you. Tell me what you're most concerned about, and we can address it together.",
            "Fear is a normal response. But you're safe here, and we'll work through this at your pace.",
        ],
        "description": "Patient expresses fear or anxiety",
        "relevance_score": 0.85,
    },
    {
        "query_pattern": "pain",
        "intent_category": "discomfort",
        "keywords": ["pain", "hurt", "aching", "sore", "uncomfortable", "discomfort"],
        "responses": [
            "I'm sorry you're experiencing pain. Let's focus on gentle, breathing-based techniques that might help you find some relief.",
            "Pain can be a barrier to relaxation. Let's try progressive muscle relaxation or visualization to help your body find comfort.",
            "It's important that you're comfortable. Would adjusting your position or pace help, or would guided imagery work better?",
            "Let's use breathing techniques to help your body relax and potentially ease some of that discomfort.",
        ],
        "description": "Patient mentions pain or physical discomfort",
        "relevance_score": 0.8,
    },
    {
        "query_pattern": "struggling",
        "intent_category": "difficulty",
        "keywords": ["struggling", "difficult", "hard", "tough", "cant do", "can't do"],
        "responses": [
            "It's okay if this feels hard. These techniques take practice, and everyone finds their own way into relaxation.",
            "What you're finding difficult might actually be a sign you're being honest with yourself. Let's try a different approach.",
            "There's no wrong way to do this. Some people need different techniques. What if we tried something else?",
            "You're doing great just by trying. Relaxation is a skill, and it gets easier with practice.",
        ],
        "description": "Patient expresses difficulty with the process",
        "relevance_score": 0.8,
    },
    {
        "query_pattern": "distracted",
        "intent_category": "focus",
        "keywords": ["distracted", "cant focus", "can't focus", "mind wandering", "thoughts everywhere"],
        "responses": [
            "It's completely normal for your mind to wander—that's actually one of the first things we work on. Just gently guide it back.",
            "Distraction is part of the process. When you notice your mind wandering, that awareness itself is progress. Bring it back gently.",
            "Many people find it hard to focus at first. That's why we use techniques like anchoring to your breath. Let's try that.",
            "Your mind might be busy processing thoughts. That's okay. Let's use a specific focal point to help calm it.",
        ],
        "description": "Patient has difficulty concentrating or maintaining focus",
        "relevance_score": 0.75,
    },
    {
        "query_pattern": "tired",
        "intent_category": "fatigue",
        "keywords": ["tired", "exhausted", "sleepy", "fatigued", "worn out", "drained"],
        "responses": [
            "It's okay if you're feeling tired. Relaxation can sometimes bring that fatigue to the surface—it's your body asking for rest.",
            "Tiredness during guided relaxation is actually a good sign—it means your nervous system is responding. Let's continue gently.",
            "If you're too tired right now, we can take a break and come back when you have more energy. What feels right?",
            "Relaxation naturally reduces stimulation, and sometimes that leads to tiredness. You're doing exactly what you should be doing.",
        ],
        "description": "Patient expresses fatigue or drowsiness",
        "relevance_score": 0.7,
    },
    {
        "query_pattern": "overwhelmed",
        "intent_category": "stress",
        "keywords": ["overwhelmed", "too much", "stressed", "stressed out", "can't handle", "cant handle"],
        "responses": [
            "Feeling overwhelmed is a signal that we need to slow things down. Let's pause and take it one small breath at a time.",
            "When overwhelm happens, simplicity helps. Let's focus just on breathing—nothing else matters right now.",
            "You're not alone in this feeling. Many people feel overwhelmed during treatment. We can make this process smaller and simpler.",
            "Let's break this into tiny, manageable pieces. Right now, all you need to focus on is this one breath.",
        ],
        "description": "Patient feels overwhelmed by stress or circumstances",
        "relevance_score": 0.85,
    },
]


def seed_database():
    """Seed response templates into the database."""
    db = SessionLocal()

    try:
        # Count existing templates
        existing_count = db.query(ResponseTemplate).count()
        logger.info(f"Existing templates: {existing_count}")

        # Add templates
        for template_data in TEMPLATES:
            # Check if already exists
            existing = db.query(ResponseTemplate).filter(
                ResponseTemplate.query_pattern == template_data["query_pattern"]
            ).first()

            if existing:
                logger.info(f"Skipping existing template: {template_data['query_pattern']}")
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
            logger.info(f"Added template: {template_data['query_pattern']}")

        db.commit()
        logger.info("✅ Seeding complete!")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding database: {str(e)}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
