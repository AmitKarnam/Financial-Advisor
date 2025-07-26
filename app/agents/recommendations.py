# agents/recommendations.py
import logging
from typing import Dict, Any
from ..services.gemini_client import query_gemini

RECOMMENDATION_PROMPT = """
You are a financial recommendation agent. Based on the user's structured financial profile (JSON below) and current market conditions, suggest suitable investment instruments and strategies for the user's goals.

Be specific and practical. Use the user's risk profile, goals, and financial situation. If you have access to live market data (MCP), incorporate it. If not, use general best practices for the current market environment.

Return your recommendations as a plain text summary, not JSON. Be clear, concise, and actionable.

User Profile JSON:
{profile_json}
"""

async def generate_recommendations(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate investment recommendations using LLM and (optionally) MCP data.
    """
    import json
    try:
        logging.info("[RECOMMENDATION AGENT] Received profile for recommendations:")
        logging.info(json.dumps(profile, indent=2))
        prompt = RECOMMENDATION_PROMPT.format(profile_json=json.dumps(profile, indent=2))
        logging.info("[RECOMMENDATION AGENT] Prompt sent to LLM:")
        logging.info(prompt)
        messages = [{"role": "user", "parts": [{"text": prompt}]}]
        result = await query_gemini(messages)
        logging.info(f"[RECOMMENDATION AGENT] Raw LLM response: {result}")
        recommendations_text = ""
        if result.get('candidates') and result['candidates'][0].get('content'):
            recommendations_text = result['candidates'][0]['content']['parts'][0].get('text', '')
            logging.info(f"[RECOMMENDATION AGENT] Final recommendations text: {recommendations_text}")
        return {
            "recommendations_text": recommendations_text,
            "timestamp": str(logging.Formatter().formatTime(logging.makeLogRecord({})))
        }
    except Exception as e:
        logging.error(f"Error generating recommendations: {e}")
        return {
            "recommendations_text": "I apologize, but I encountered an issue generating specific recommendations. Please try again later.",
            "error": str(e),
            "timestamp": str(logging.Formatter().formatTime(logging.makeLogRecord({})))
        }
