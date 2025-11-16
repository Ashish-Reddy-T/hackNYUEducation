"""
Socrates Node - Main Socratic tutoring logic.
Generates questions, analogies, and guidance without giving direct answers.
"""
import logging

from app.config import settings
from app.graph.state import RoutingDecision, TutorMode, TutorState, VisualAction, get_conversation_context
from app.services.gemini_client import gemini_service

logger = logging.getLogger(__name__)


SOCRATIC_SYSTEM_PROMPT = """You are Agora, a Socratic tutor helping students learn through guided questioning.

CORE PRINCIPLES:
1. NEVER give direct answers immediately
2. Ask guiding questions that lead students to discover answers themselves
3. Use analogies and examples to build understanding
4. Encourage students to explain their thinking
5. Only provide direct explanations if frustration is high (frustration_level >= 3)

YOUR APPROACH:
- Break complex topics into smaller questions
- Build on what the student already knows
- Use the "What do you think?" pattern
- Validate correct reasoning enthusiastically
- Gently correct misconceptions with questions

RESPONSE FORMAT:
You may optionally suggest visual aids. If you want to create a sticky note on the whiteboard, include:
[VISUAL: CREATE_NOTE | text: "note text" | x: 100 | y: 200]

Keep responses conversational, warm, and encouraging.
Use simple language appropriate for the topic.
"""


def build_socratic_prompt(state: TutorState) -> str:
    """
    Build the full prompt for Socratic response generation.
    
    Args:
        state: Current tutor state
    
    Returns:
        Complete prompt string
    """
    logger.debug("Building Socratic prompt")
    
    # Conversation context
    context = get_conversation_context(state, max_turns=5)
    
    # RAG context
    rag_text = ""
    if state["rag_context"]:
        rag_chunks = []
        for idx, ctx in enumerate(state["rag_context"][:3], 1):
            rag_chunks.append(f"[Note {idx}] {ctx['text']}")
        rag_text = "\n".join(rag_chunks)
    
    # Memory context
    memory_text = ""
    if state.get("memory_summary"):
        memory = state["memory_summary"]
        if memory["mastered"]:
            memory_text += f"Student has mastered: {', '.join(memory['mastered'])}\n"
        if memory["confused"]:
            memory_text += f"Student struggles with: {', '.join(memory['confused'])}\n"
    
    # Frustration context
    frustration_note = ""
    if state["frustration_level"] >= settings.frustration_threshold:
        frustration_note = f"\n⚠️ FRUSTRATION LEVEL HIGH ({state['frustration_level']}/5): Provide more direct guidance."
    
    # Build full prompt
    prompt = f"""CONTEXT:
{context}

STUDENT'S CURRENT INPUT: {state['last_user_text']}

RELEVANT NOTES:
{rag_text if rag_text else "No specific notes retrieved."}

STUDENT KNOWLEDGE:
{memory_text if memory_text else "No historical data yet."}

ROUTING: {state['routing'].value if state['routing'] else 'unknown'}
MODE: {state['mode'].value}
{frustration_note}

Generate your Socratic response:"""
    
    logger.debug("Socratic prompt built", extra={
        "prompt_length": len(prompt),
        "has_rag": bool(rag_text),
        "has_memory": bool(memory_text),
        "frustration_level": state["frustration_level"]
    })
    
    return prompt


def extract_visual_actions(response_text: str) -> tuple[str, list[VisualAction]]:
    """
    Extract visual action commands from response text.
    
    Args:
        response_text: Generated response
    
    Returns:
        Tuple of (cleaned_text, visual_actions)
    """
    import re
    
    visual_actions: list[VisualAction] = []
    cleaned_text = response_text
    
    # Find all [VISUAL: ...] patterns
    pattern = r'\[VISUAL:\s*CREATE_NOTE\s*\|\s*text:\s*"([^"]+)"\s*\|\s*x:\s*(\d+)\s*\|\s*y:\s*(\d+)\]'
    matches = re.finditer(pattern, response_text)
    
    for match in matches:
        text = match.group(1)
        x = int(match.group(2))
        y = int(match.group(3))
        
        visual_action: VisualAction = {
            "action": "CREATE_NOTE",
            "payload": {
                "text": text,
                "x": x,
                "y": y
            }
        }
        visual_actions.append(visual_action)
        
        logger.debug("Visual action extracted", extra={
            "action": "CREATE_NOTE",
            "text_preview": text[:50],
            "position": (x, y)
        })
    
    # Remove visual commands from text
    cleaned_text = re.sub(pattern, '', cleaned_text).strip()
    
    return cleaned_text, visual_actions


async def socrates_node(state: TutorState) -> TutorState:
    """
    Generate Socratic response using Gemini.
    
    Args:
        state: Current tutor state
    
    Returns:
        Updated state with response
    """
    try:
        logger.debug("=== SOCRATES NODE START ===")
        logger.debug("Socrates node processing", extra={
            "user_id": state["user_id"],
            "session_id": state["session_id"],
            "routing": state.get("routing"),
            "mode": state["mode"],
            "frustration_level": state["frustration_level"]
        })
        
        # Build prompt
        prompt = build_socratic_prompt(state)
        
        logger.debug("Calling Gemini for Socratic response...")
        
        # Generate response
        response = await gemini_service.generate_text(
            prompt=prompt,
            system_prompt=SOCRATIC_SYSTEM_PROMPT,
            temperature=settings.gemini_temperature,
            max_tokens=settings.gemini_max_tokens
        )
        
        logger.debug("Gemini response generated", extra={
            "response_length": len(response)
        })
        
        # Extract visual actions
        cleaned_response, visual_actions = extract_visual_actions(response)
        
        state["response_text"] = cleaned_response
        state["visual_actions"] = visual_actions
        state["should_tts"] = True
        
        logger.info("Socratic response generated", extra={
            "response_length": len(cleaned_response),
            "visual_actions_count": len(visual_actions),
            "frustration_level": state["frustration_level"]
        })
        
        # Log response preview
        logger.debug("Response preview", extra={
            "preview": cleaned_response[:200]
        })
        
        logger.debug("=== SOCRATES NODE END ===")
        
        return state
        
    except Exception as e:
        logger.error("Socrates node failed", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "user_id": state.get("user_id")
        }, exc_info=True)
        
        # Fallback response
        state["response_text"] = "I'm having trouble processing that. Could you rephrase your question?"
        state["visual_actions"] = []
        state["should_tts"] = True
        state["error"] = f"Socrates error: {str(e)}"
        
        return state


logger.debug("Socrates node module loaded")
