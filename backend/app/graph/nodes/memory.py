"""
Memory Node - Manages student understanding tracking.
Loads historical memory and updates based on interactions.
"""
import logging
import time

from app.config import settings
from app.graph.state import MemorySummary, TutorState, get_conversation_context
from app.services.gemini_client import gemini_service
from app.services.qdrant_client import qdrant_service

logger = logging.getLogger(__name__)


MEMORY_ANALYSIS_PROMPT = """You are analyzing a tutoring conversation to understand what the student has mastered vs what they're confused about.

Analyze the recent conversation and identify:
1. Topics the student clearly understands (mastered)
2. Topics the student is struggling with or confused about

Respond with ONLY valid JSON in this format:
{
  "mastered": ["topic1", "topic2"],
  "confused": ["topic3", "topic4"]
}

Be specific. Extract actual topic names from the conversation, not generic descriptions."""


async def load_memory_node(state: TutorState) -> TutorState:
    """
    Load historical memory summaries for the student.
    
    Args:
        state: Current tutor state
    
    Returns:
        Updated state with memory summary
    """
    try:
        logger.debug("=== LOAD MEMORY NODE START ===")
        logger.debug("Loading memory", extra={
            "user_id": state["user_id"],
            "session_id": state["session_id"]
        })
        
        # Retrieve memories from Qdrant
        memories = await qdrant_service.get_memory(
            user_id=state["user_id"],
            limit=5
        )
        
        logger.debug("Memories retrieved", extra={
            "memories_count": len(memories)
        })
        
        if not memories:
            logger.info("No historical memory found, initializing empty", extra={
                "user_id": state["user_id"]
            })
            state["memory_summary"] = {
                "mastered": [],
                "confused": [],
                "last_updated": time.time()
            }
            return state
        
        # Aggregate memories
        all_mastered = []
        all_confused = []
        
        for memory in memories:
            memory_data = memory.get("memory_data", {})
            all_mastered.extend(memory_data.get("mastered", []))
            all_confused.extend(memory_data.get("confused", []))
        
        # Deduplicate
        all_mastered = list(set(all_mastered))
        all_confused = list(set(all_confused))
        
        # Remove items from confused if they're now mastered
        all_confused = [topic for topic in all_confused if topic not in all_mastered]
        
        logger.info("Memory loaded and aggregated", extra={
            "mastered_count": len(all_mastered),
            "confused_count": len(all_confused),
            "memories_processed": len(memories)
        })
        
        state["memory_summary"] = {
            "mastered": all_mastered,
            "confused": all_confused,
            "last_updated": time.time()
        }
        
        logger.debug("=== LOAD MEMORY NODE END ===")
        
        return state
        
    except Exception as e:
        logger.error("Load memory node failed", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "user_id": state.get("user_id")
        }, exc_info=True)
        
        # Initialize empty memory
        state["memory_summary"] = {
            "mastered": [],
            "confused": [],
            "last_updated": time.time()
        }
        state["error"] = f"Memory load error: {str(e)}"
        
        return state


async def update_memory_node(state: TutorState) -> TutorState:
    """
    Update memory based on recent conversation.
    Called periodically (every N turns).
    
    Args:
        state: Current tutor state
    
    Returns:
        Updated state with refreshed memory
    """
    try:
        logger.debug("=== UPDATE MEMORY NODE START ===")
        logger.debug("Updating memory", extra={
            "user_id": state["user_id"],
            "session_id": state["session_id"],
            "turn_count": state["turn_count"]
        })
        
        # Check if update is needed
        update_interval = settings.memory_update_interval
        if state["turn_count"] % update_interval != 0:
            logger.debug("Skipping memory update - not at interval", extra={
                "turn_count": state["turn_count"],
                "interval": update_interval
            })
            return state
        
        # Get recent conversation
        context = get_conversation_context(state, max_turns=update_interval)
        
        if not context or context.strip() == "":
            logger.warning("Empty conversation context, skipping memory update")
            return state
        
        logger.debug("Analyzing conversation for memory update", extra={
            "context_length": len(context),
            "turns_analyzed": min(update_interval * 2, len(state["messages"]))
        })
        
        # Analyze with Gemini
        prompt = f"""Recent Conversation:
{context}

Analyze this conversation:"""
        
        logger.debug("Calling Gemini for memory analysis...")
        
        memory_json = await gemini_service.generate_json(
            prompt=prompt,
            system_prompt=MEMORY_ANALYSIS_PROMPT
        )
        
        logger.debug("Memory analysis completed", extra={
            "mastered_count": len(memory_json.get("mastered", [])),
            "confused_count": len(memory_json.get("confused", []))
        })
        
        # Merge with existing memory
        current_memory = state.get("memory_summary") or {
            "mastered": [],
            "confused": [],
            "last_updated": 0.0
        }
        
        new_mastered = list(set(current_memory["mastered"] + memory_json.get("mastered", [])))
        new_confused = list(set(current_memory["confused"] + memory_json.get("confused", [])))
        
        # Remove confused topics that are now mastered
        new_confused = [topic for topic in new_confused if topic not in new_mastered]
        
        updated_memory = {
            "mastered": new_mastered,
            "confused": new_confused,
            "last_updated": time.time()
        }
        
        state["memory_summary"] = updated_memory
        
        logger.info("Memory updated successfully", extra={
            "mastered_count": len(new_mastered),
            "confused_count": len(new_confused),
            "new_mastered": memory_json.get("mastered", []),
            "new_confused": memory_json.get("confused", [])
        })
        
        # Generate embedding and store in Qdrant
        memory_text = f"Mastered: {', '.join(new_mastered)}. Confused: {', '.join(new_confused)}."
        
        logger.debug("Embedding and storing memory in Qdrant...")
        
        embedding = await gemini_service.embed_text(memory_text)
        
        await qdrant_service.upsert_memory(
            user_id=state["user_id"],
            session_id=state["session_id"],
            memory_data=updated_memory,
            embedding=embedding
        )
        
        logger.info("Memory persisted to Qdrant", extra={
            "user_id": state["user_id"],
            "session_id": state["session_id"]
        })
        
        logger.debug("=== UPDATE MEMORY NODE END ===")
        
        return state
        
    except Exception as e:
        logger.error("Update memory node failed", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "user_id": state.get("user_id")
        }, exc_info=True)
        
        state["error"] = f"Memory update error: {str(e)}"
        
        return state


logger.debug("Memory node module loaded")
