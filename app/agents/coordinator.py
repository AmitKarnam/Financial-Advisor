# app/agents/coordinator.py
from enum import Enum
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from .conversations import handle_user_message as conversation_handler, get_chat_history, chat_history
from ..utils.sse import create_sse_event

class WorkflowStage(Enum):
    CONVERSATION = "conversation"
    PROFILE_EXTRACTION = "profile_extraction"
    RECOMMENDATION = "recommendation"
    COMPLETE = "complete"

class AgentCoordinator:
    def __init__(self):
        self.current_stage = WorkflowStage.CONVERSATION
        self.user_profile = None
        self.recommendations = None
        self.profile_extracted_at = None
        self.recommendations_generated_at = None
        self.conversation_turn_count = 0
        
    async def process_user_input(self, user_message: str = None):
        """Main entry point for processing user input through the agent workflow"""
        logging.info(f"[COORDINATOR] Current stage: {self.current_stage.value}")
        if self.current_stage == WorkflowStage.CONVERSATION:
            logging.info("[COORDINATOR] Handling CONVERSATION stage.")
            return await self._handle_conversation_stage(user_message)
        elif self.current_stage == WorkflowStage.PROFILE_EXTRACTION:
            logging.info("[COORDINATOR] Handling PROFILE_EXTRACTION stage.")
            return await self._handle_profile_extraction_stage()
        elif self.current_stage == WorkflowStage.RECOMMENDATION:
            logging.info("[COORDINATOR] Handling RECOMMENDATION stage.")
            return await self._handle_recommendation_stage()
        elif self.current_stage == WorkflowStage.COMPLETE:
            logging.info("[COORDINATOR] Handling COMPLETE stage (follow-up questions).")
            return await self._handle_followup_questions(user_message)
        else:
            logging.info("[COORDINATOR] Unknown stage, sending status response.")
            return await self._create_status_response()
    
    async def _handle_conversation_stage(self, user_message: str = None):
        """Handle the conversation stage with profile gathering"""
        response_stream = await conversation_handler(user_message)
        async def stream():
            async for chunk in response_stream:
                # Signal-based transition: look for PROFILE_COMPLETE_SIGNAL in output
                if chunk and "PROFILE_COMPLETE_SIGNAL" in chunk:
                    logging.info("[COORDINATOR] PROFILE_COMPLETE_SIGNAL detected in conversation stream. Transitioning to PROFILE_EXTRACTION stage.")
                    self.current_stage = WorkflowStage.PROFILE_EXTRACTION
                    yield await create_sse_event("\n---\n\n[COORDINATOR] PROFILE_COMPLETE_SIGNAL detected. Moving to summary agent...")
                    logging.info("[COORDINATOR] Extracting profile using summary agent (signal-based).")
                    await self._extract_profile()
                    yield await create_sse_event("\nProfile extracted successfully!")
                    logging.info("[COORDINATOR] Transitioning to RECOMMENDATION stage.")
                    yield await create_sse_event("\n---\n\n[COORDINATOR] Moving to recommendation agent...")
                    self.current_stage = WorkflowStage.RECOMMENDATION
                    # Stream recommendations to frontend
                    async for next_chunk in self._handle_recommendation_stage():
                        yield next_chunk
                    # Do not return here; let the generator finish naturally
                yield chunk
        if user_message:
            self.conversation_turn_count += 1
            logging.info(f"[COORDINATOR] Conversation turn count: {self.conversation_turn_count}")
        # Fallback: if signal not detected, use completeness check
        if self.conversation_turn_count >= 4:
            is_complete = await self._is_profile_complete()
            logging.info(f"[COORDINATOR] Profile completeness check result: {is_complete}")
            if is_complete:
                logging.info("[COORDINATOR] Sufficient information gathered. Transitioning to PROFILE_EXTRACTION stage.")
                self.current_stage = WorkflowStage.PROFILE_EXTRACTION
                # Yield profile extraction and recommendation events in order
                async def combined_stream():
                    await self._extract_profile()
                    yield await create_sse_event("\nProfile extracted successfully!")
                    self.current_stage = WorkflowStage.RECOMMENDATION
                    async for next_chunk in self._handle_recommendation_stage():
                        yield next_chunk
                # Do not return here; let the generator finish naturally
        return stream()
    
    async def _create_enhanced_stream_with_transition(self, original_stream):
        async def enhanced_stream():
            async for chunk in original_stream:
                yield chunk
            yield await create_sse_event("\n\n---\n\n**Analysis Complete!** I have all the information I need. Let me now:")
            yield await create_sse_event("\nExtract and organize your financial profile...")
            logging.info("[COORDINATOR] Extracting profile using summary agent.")
            await self._extract_profile()
            yield await create_sse_event("\nProfile extracted successfully!")
            logging.info("[COORDINATOR] Transitioning to RECOMMENDATION stage.")
            self.current_stage = WorkflowStage.RECOMMENDATION
            # Immediately start recommendation stage after profile extraction
            async for chunk in self._handle_recommendation_stage():
                yield chunk
        # Do not return here; let the generator finish naturally
        return enhanced_stream()
    async def _handle_profile_extraction_stage(self):
        logging.info("[COORDINATOR] PROFILE_EXTRACTION stage: extracting profile.")
        await self._extract_profile()
        self.current_stage = WorkflowStage.RECOMMENDATION
        logging.info("[COORDINATOR] Transitioning to RECOMMENDATION stage.")
        # Immediately start recommendation stage after profile extraction
        # Return a generator that yields both profile extraction and recommendation events
        async def combined_stream():
            yield await create_sse_event("\nProfile extracted successfully!")
            async for chunk in self._handle_recommendation_stage():
                yield chunk
        # Do not return here; let the generator finish naturally
        return combined_stream()
    async def _handle_recommendation_stage(self):
        logging.info("[COORDINATOR] Entering _handle_recommendation_stage")
        try:
            from .recommendations import generate_recommendations
            if self.user_profile:
                self.recommendations = await generate_recommendations(self.user_profile)
                self.recommendations_generated_at = datetime.now()
                logging.info(f"Recommendations generated successfully at {self.recommendations_generated_at}")
                recommendations_text = self.recommendations.get('recommendations_text', '')
                chat_msg = f"\n**Your Personalized Financial Recommendations:**\n\n{recommendations_text}\n\n---\n\n💬 **What's Next?** Feel free to ask me any questions about these recommendations or request clarification on any specific points!"
                chat_history.append({"role": "model", "parts": [{"text": chat_msg}]})
                self.current_stage = WorkflowStage.COMPLETE
                logging.info("[COORDINATOR] Streaming recommendations to frontend")
                logging.info("[COORDINATOR] Exiting _handle_recommendation_stage (COMPLETE)")
                yield await create_sse_event(chat_msg)
                # Do not return here; let the generator finish naturally
            else:
                logging.info("[COORDINATOR] No user profile, cannot generate recommendations")
                self.current_stage = WorkflowStage.COMPLETE
                logging.info("[COORDINATOR] Exiting _handle_recommendation_stage (COMPLETE - error)")
                yield await create_sse_event("I apologize, but I couldn't generate specific recommendations at this time. Please try asking me specific questions about your financial situation.")
                # Do not return here; let the generator finish naturally
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            self.current_stage = WorkflowStage.COMPLETE
            logging.info("[COORDINATOR] Exiting _handle_recommendation_stage (COMPLETE - fallback)")
            yield await create_sse_event("I apologize, but I encountered an issue generating specific recommendations. Please try again later.")
            # Do not return here; let the generator finish naturally
    
    async def _is_profile_complete(self) -> bool:
        """
        Determine if enough information has been gathered using your existing Gemini setup
        """
        try:
            from ..services.gemini_client import query_gemini
            
            # Get conversation history
            history = get_chat_history()    
            
            if len(history) < 4:  # Need minimum conversation
                return False
            
            # Build conversation text
            conversation_text = ""
            for msg in history:
                role = msg.get("role", "")
                if role in ["user", "model"]:
                    parts = msg.get("parts", [])
                    if parts and "text" in parts[0]:
                        speaker = "User" if role == "user" else "Assistant"
                        conversation_text += f"{speaker}: {parts[0]['text']}\n"
            
            # Check completeness using LLM
            completeness_prompt = f"""
            Analyze this financial conversation and determine if we have gathered enough information to create a comprehensive financial profile.

            We need information about:
            1. Current financial situation (income, expenses, savings, job, location)
            2. Financial goals (short-term, medium-term, long-term)
            3. Risk tolerance and investment experience
            4. Lifestyle preferences and future aspirations

            Conversation:
            {conversation_text}

            Respond with only one word: "COMPLETE" if we have sufficient information across most categories, or "INCOMPLETE" if we need more information in major categories.
            """
            
            messages = [{"role": "user", "parts": [{"text": completeness_prompt}]}]
            result = await query_gemini(messages)
            
            if result.get('candidates') and result['candidates'][0].get('content'):
                response = result['candidates'][0]['content']['parts'][0].get('text', '').strip().upper()
                return response == "COMPLETE"
                
        except Exception as e:
            logging.error(f"Error checking conversation completeness: {e}")
        
        # Fallback: check based on conversation length and keyword presence
        return self.conversation_turn_count >= 8
    
    async def _extract_profile(self):
        """Extract structured profile from conversation history using summary agent"""
        try:
            from .summary import extract_profile_from_conversation
            conversation_history = get_chat_history()
            self.user_profile = await extract_profile_from_conversation(conversation_history)
            self.profile_extracted_at = datetime.now()
            logging.info(f"Profile extracted successfully at {self.profile_extracted_at}")
        except Exception as e:
            logging.error(f"Error in profile extraction: {e}")
            self.user_profile = {"error": "Could not extract profile", "timestamp": datetime.now().isoformat()}
    
    
    async def _handle_followup_questions(self, user_message: str):
        response_stream = await conversation_handler(user_message)
        async def stream():
            async for chunk in response_stream:
                yield chunk
        return stream()
    
    async def _create_status_response(self):
        """Create a status response for processing states"""
        status_messages = {
            WorkflowStage.PROFILE_EXTRACTION: "🔄 Analyzing your financial profile...",
            WorkflowStage.RECOMMENDATION: "💡 Generating personalized investment recommendations..."
        }
        message = status_messages.get(self.current_stage, "Processing...")
        async def status_stream():
            yield await create_sse_event(message)
        return status_stream()
    
    def reset(self):
        """Reset the coordinator state"""
        self.current_stage = WorkflowStage.CONVERSATION
        self.user_profile = None
        self.recommendations = None
        self.profile_extracted_at = None
        self.recommendations_generated_at = None
        self.conversation_turn_count = 0
        chat_history.clear()

# Global coordinator instance
coordinator = AgentCoordinator()

async def handle_user_input(user_message: str = None):
    """Main handler that your FastAPI routes will use"""
    return await coordinator.process_user_input(user_message)

async def get_workflow_status():
    """Get current workflow status"""
    return {
        "current_stage": coordinator.current_stage.value,
        "profile_extracted": coordinator.user_profile is not None,
        "recommendations_ready": coordinator.recommendations is not None,
        "conversation_turns": coordinator.conversation_turn_count,
        "profile_extracted_at": coordinator.profile_extracted_at.isoformat() if coordinator.profile_extracted_at else None,
        "recommendations_generated_at": coordinator.recommendations_generated_at.isoformat() if coordinator.recommendations_generated_at else None
    }

async def reset_workflow():
    """Reset the workflow"""
    coordinator.reset()
    return {
        "status": "reset_complete",
        "message": "Conversation has been reset. You can start a new financial planning session."
    }