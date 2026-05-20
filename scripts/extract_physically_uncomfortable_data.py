"""
Extract data from "Physically Uncomfortable / Not Ready" document
and structure it for database insertion.

This script reads the docx and creates:
1. States (with severity levels: mild, moderate, severe)
2. LibraryItems (scripts, techniques, safe places)
3. ResponseTemplates (for RAG retrieval)
4. Process definition
"""

from docx import Document
import json

doc = Document('/sessions/upbeat-kind-pasteur/mnt/uploads/Physically uncomfortable Version2 (Ado)-c624e337.docx')

# ===== EXTRACT DATA =====

# 1. STATES WITH SEVERITY LEVELS
states = {
    "physically_uncomfortable_mild": {
        "code": "physically_uncomfortable_mild",
        "name": "Physically Uncomfortable (Mild)",
        "description": "Slight discomfort but patient may still engage with support",
        "severity": "mild"
    },
    "physically_uncomfortable_moderate": {
        "code": "physically_uncomfortable_moderate",
        "name": "Physically Uncomfortable (Moderate)",
        "description": "May interfere with relaxation and require repositioning or brief intervention",
        "severity": "moderate"
    },
    "physically_uncomfortable_severe": {
        "code": "physically_uncomfortable_severe",
        "name": "Physically Uncomfortable (Severe)",
        "description": "Significant distress or symptoms that may prevent safe participation",
        "severity": "severe"
    },
}

# 2. EXTRACT CLIENT RESPONSES FROM TABLES
client_responses = []
for table_idx, table in enumerate(doc.tables):
    for row in table.rows:
        for cell in row.cells:
            text = cell.text.strip()
            if text and text.startswith('"'):
                # Split by newlines to get individual responses
                responses = text.split('\n')
                for resp in responses:
                    resp = resp.strip().strip('"')
                    if resp and len(resp) > 10:
                        client_responses.append(resp)

# Remove duplicates while preserving order
seen = set()
unique_responses = []
for r in client_responses:
    if r not in seen:
        seen.add(r)
        unique_responses.append(r)

# 3. AGENTIC AI SCRIPTS FOR EACH SEVERITY
agentic_scripts = {
    "introduction": {
        "kind": "introduction_script",
        "title": "Welcome & Comfort Check",
        "body": """Welcome to your Guided Imagery experience.

Guided imagery is a gentle relaxation technique that uses your imagination to help your mind and body feel calmer and more at ease. There's no right or wrong way to experience it—just allow yourself to follow along in a way that feels comfortable for you.

You may begin to notice a sense of relaxation, clarity, or calm as we continue.

Before we start, I just want to check—are you feeling comfortable right now? If you need to adjust your position or have any questions, please feel free to tell me.""",
        "metadata": {"category": "opening", "severity": "all"}
    },
    "clarifying_mild": {
        "kind": "clarification_script",
        "title": "Clarify Discomfort (Mild)",
        "body": """Can you tell me where you're feeling the discomfort?

How would you describe it—sharp, dull, pressure, aching?

When did it start?

Is it constant or does it come and go?""",
        "metadata": {"category": "clarification", "severity": "mild"}
    },
    "clarifying_moderate": {
        "kind": "clarification_script",
        "title": "Clarify Discomfort (Moderate)",
        "body": """I notice you're experiencing some physical discomfort. Let's understand what's happening so we can make adjustments.

Can you point to or describe where you're feeling this?

On a scale of 1-10, how intense is it right now?

Does it feel better when you move, or does movement make it worse?

Would shifting your position help, or do you need a brief pause before we continue?""",
        "metadata": {"category": "clarification", "severity": "moderate"}
    },
    "clarifying_severe": {
        "kind": "clarification_script",
        "title": "Clarify Discomfort (Severe)",
        "body": """I want to make sure you're safe and comfortable. The discomfort you're describing is important for me to understand.

Where exactly are you feeling this discomfort?

Can you describe it? (sharp, dull, pressure, burning, etc.)

Is this something you've experienced before, or is it new?

Are you experiencing any difficulty breathing, dizziness, or chest tightness?

If your symptoms don't ease in the next few minutes, we may need to pause this session and try again when you're feeling better.""",
        "metadata": {"category": "clarification", "severity": "severe"}
    },
}

# 4. TECHNIQUES / GROUNDING SCRIPTS
techniques = {
    "breathing_basic": {
        "kind": "technique_script",
        "title": "Basic Breathing Technique",
        "body": """Let's start with your breath—it's the simplest tool you have right now.

Breathe in slowly through your nose for a count of 4.
Hold it for just a moment.
Then exhale gently through your mouth for a count of 6.

The slower exhale helps calm your nervous system. Repeat this rhythm a few times.

Notice how your body feels with each breath—there's no forcing, just gentle breathing.""",
        "metadata": {"category": "breathing", "duration": "3-5 minutes"}
    },
    "grounding_5senses": {
        "kind": "technique_script",
        "title": "5 Senses Grounding (For Distraction)",
        "body": """Let's ground you in this moment using all your senses. This can help bring your mind away from the discomfort.

Notice 5 things you can see right now.
Notice 4 things you can physically feel (the chair, temperature, texture).
Notice 3 things you can hear.
Notice 2 things you can smell (or imagine smelling).
Notice 1 thing you can taste.

Take your time with each one. This helps anchor you in the present.""",
        "metadata": {"category": "grounding", "duration": "5 minutes"}
    },
    "progressive_muscle_relaxation": {
        "kind": "technique_script",
        "title": "Progressive Muscle Relaxation (Modified)",
        "body": """If your body feels tense, this technique can help release that tension gently.

We'll tense a muscle group for just 2 seconds, then release it. Start with your hands:

Make fists with both hands—squeeze for just 2 seconds.
Now release completely and notice the relief.

Continue this with: shoulders, face, legs, and back (but AVOID any area that's already painful).

The contrast between tension and release helps your body recognize and let go of stress.""",
        "metadata": {"category": "relaxation", "duration": "10 minutes"}
    },
}

# 5. SAFE PLACES / IMAGERY SCRIPTS
safe_places = {
    "nature_based": {
        "kind": "guided_imagery",
        "title": "Nature-Based Safe Place",
        "body": """Imagine yourself in a natural place where you feel completely safe and calm.

Perhaps a quiet beach at sunrise with gentle waves...
or a shaded forest with soft light filtering through the trees...
or a peaceful mountain top with fresh, cool air...
or a meadow filled with wildflowers swaying in the breeze.

See it in your mind. Feel the temperature, the textures around you.
Hear any gentle sounds—waves, birds, rustling leaves.

This is your safe place. You can return here anytime you need calm.""",
        "metadata": {"category": "imagery", "type": "nature"}
    },
    "comfort_spaces": {
        "kind": "guided_imagery",
        "title": "Comfort & Shelter Space",
        "body": """Imagine a cozy, comforting space—somewhere you feel held and safe.

Maybe it's a cozy room with soft blankets and warm lighting...
a window seat during gentle rain...
sitting by a fireplace on a cold evening...
a quiet library filled with books you love...
a hammock swinging slowly between trees.

Let yourself settle into this space. Feel the comfort around you.
Your body is supported. You are safe here.""",
        "metadata": {"category": "imagery", "type": "comfort"}
    },
    "healing_light": {
        "kind": "guided_imagery",
        "title": "Healing Light Visualization",
        "body": """Imagine a warm, healing light—perhaps golden or soft white—surrounding any area of discomfort in your body.

This light is gentle, soothing, and warm.
It doesn't erase the discomfort, but it brings a sense of ease and care to that area.

See the light expanding, creating space around the discomfort.
You don't have to fight it or push it away—just let the light be there with it.

As you breathe, imagine the light becoming even softer, even more soothing.""",
        "metadata": {"category": "imagery", "type": "healing"}
    },
}

# 6. RESPONSE TEMPLATES (FOR RAG)
response_templates = {
    "physically_uncomfortable": {
        "query_pattern": "physically uncomfortable",
        "intent_category": "discomfort",
        "keywords": [
            "uncomfortable", "pain", "ache", "tension", "stiff", "sore", "cramped",
            "pressure", "tight", "heavy", "weak", "sensitive", "uneasy", "tense"
        ],
        "responses": [
            "That's completely understandable. Physical discomfort can make relaxation harder. Let's see what adjustments might help.",
            "Thank you for letting me know. Your comfort matters. Would shifting your position, adjusting your posture, or taking a brief pause help?",
            "I'm glad you told me. Sometimes our bodies need a moment to settle before we can fully relax. What would feel better right now?",
            "Discomfort is real, and I hear you. Let's work with what your body needs right now—maybe some breathing, movement, or a different technique.",
        ],
        "description": "Patient expresses physical discomfort or pain",
        "relevance_score": 0.95,
    },
    "not_ready": {
        "query_pattern": "not ready",
        "intent_category": "hesitation",
        "keywords": ["not ready", "not prepared", "need more time", "not yet", "hesitant"],
        "responses": [
            "That's okay. It's important to start when you feel ready. We can take more time, or we can adjust how we begin.",
            "There's no rush. Feeling ready is important. What would help you feel more prepared?",
            "That's completely valid. Some people need a few minutes to settle in. What would help you feel ready?",
        ],
        "description": "Patient expresses hesitation or feeling unprepared",
        "relevance_score": 0.85,
    },
}

# ===== OUTPUT STRUCTURED DATA =====

output = {
    "document_name": "Physically Uncomfortable / Not Ready",
    "process_code": "physically_uncomfortable_v1",
    "description": "Comprehensive process for managing patient physical discomfort during guided imagery sessions",

    "states": states,

    "unique_patient_responses": unique_responses,
    "total_unique_responses": len(unique_responses),

    "library_items": {
        **agentic_scripts,
        **techniques,
        **safe_places,
    },

    "response_templates": response_templates,

    "summary": {
        "total_patient_response_variations": len(unique_responses),
        "severity_levels": list(states.keys()),
        "techniques_available": list(techniques.keys()),
        "safe_places_available": list(safe_places.keys()),
        "agentic_scripts_available": list(agentic_scripts.keys()),
        "response_templates_available": list(response_templates.keys()),
    }
}

# Print summary
print("\n" + "="*80)
print("EXTRACTED DATA SUMMARY")
print("="*80 + "\n")

print(f"📄 Document: {output['document_name']}")
print(f"📊 Process Code: {output['process_code']}")
print(f"\n✓ Severity Levels: {len(states)}")
for code, state in states.items():
    print(f"  - {state['name']} ({state['severity']})")

print(f"\n✓ Patient Response Variations: {len(unique_responses)}")
print(f"  Sample responses:")
for resp in unique_responses[:5]:
    print(f"    - {resp}")
print(f"  ... and {len(unique_responses) - 5} more")

print(f"\n✓ Library Items (Techniques & Scripts): {len(output['library_items'])}")
print(f"  - Agentic Scripts: {len(agentic_scripts)}")
print(f"  - Techniques: {len(techniques)}")
print(f"  - Safe Places: {len(safe_places)}")

print(f"\n✓ Response Templates (RAG): {len(response_templates)}")
for pattern, template in response_templates.items():
    print(f"  - {template['query_pattern']} ({len(template['responses'])} response options)")

print("\n" + "="*80)
print("READY TO ADD TO DATABASE?")
print("="*80)

# Save detailed output for review
with open('/tmp/extracted_data.json', 'w') as f:
    # Convert to JSON-serializable format
    json_output = {
        "document_name": output['document_name'],
        "process_code": output['process_code'],
        "description": output['description'],
        "states": output['states'],
        "unique_patient_responses_count": len(unique_responses),
        "sample_patient_responses": unique_responses[:10],
        "library_items_count": len(output['library_items']),
        "response_templates": output['response_templates'],
        "summary": output['summary'],
    }
    json.dump(json_output, f, indent=2)

print("\nDetailed data saved to: /tmp/extracted_data.json")

