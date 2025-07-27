# agents/summary.py
import json
import logging
from typing import Dict, Any, List
from ..services.gemini_client import query_gemini

PROFILE_EXTRACTION_PROMPT = """
You are a financial profile extraction agent. Your task is to analyze the conversation history and extract structured information into a specific JSON format.

Based on the conversation, fill out the following JSON schema with the information gathered. Use null for any fields where information wasn't provided or can't be inferred. Be conservative with estimates and only include information that was explicitly discussed or can be reasonably inferred.

For fields that require arrays (like goals), create appropriate objects even if some sub-fields are null.

JSON Schema to fill:
{profile_schema}

Conversation History:
{conversation_text}

Return ONLY the filled JSON object, no additional text or explanation. Ensure the JSON is valid and properly formatted.
"""

def load_profile_schema():
    """Load the profile schema from your second document"""
    return {
        "userProfile": {
            "demographics": {
                "currentAge": None,
                "targetRetirementAge": None,
                "maritalStatus": None,
                "dependents": None,
                "location": None
            },
            "financialSnapshot": {
                "monthlyIncome": None,
                "monthlyExpenses": None,
                "currentSavingsRate": None,
                "expectedIncomeGrowthRate": None,
                "jobStability": None
            },
            "investmentProfile": {
                "riskTolerance": None,
                "investmentExperience": None,
                "investmentKnowledge": None,
                "preferredInvestmentTypes": [],
                "investmentTimeHorizon": None
            },
            "behavioralTraits": {
                "savingsDiscipline": None,
                "spendingPattern": None,
                "financialGoalClarity": None,
                "moneyMotivation": None
            }
        },
        "financialGoals": {
            "shortTerm": [],
            "mediumTerm": [],
            "longTerm": []
        },
        "riskAppetite": {
            "risk_appetite_indicators": {
                "risk_tolerance_score": None,
                "risk_capacity_score": None,
                "loss_tolerance_percentage": None,
                "recovery_time_comfort": None,
                "volatility_comfort": None,
                "sleep_at_night_threshold": None
            },
            "market_behavior_patterns": {
                "bear_market_response": None,
                "bull_market_response": None,
                "market_crash_history": None,
                "fomo_susceptibility": None,
                "panic_selling_tendency": None,
                "market_timing_attempts": None
            },
            "financial_psychology": {
                "money_relationship": None,
                "biggest_financial_fear": None,
                "motivating_financial_goal": None,
                "decision_making_under_pressure": None,
                "regret_aversion": None,
                "optimism_bias": None,
                "anchoring_tendency": None
            },
            "experience_and_knowledge": {
                "years_investing": None,
                "investment_knowledge_level": None,
                "past_major_losses": None,
                "recovery_from_losses": None,
                "learning_from_mistakes": None,
                "financial_education": None
            },
            "behavioral_traits": {
                "planning_horizon": None,
                "research_depth": None,
                "herd_mentality": None,
                "patience_level": None,
                "discipline_score": None,
                "emotional_control": None,
                "diversification_understanding": None
            },
            "life_context": {
                "age": None,
                "income_stability": None,
                "dependents": None,
                "major_expenses_timeline": None,
                "career_stage": None,
                "health_status": None,
                "insurance_coverage": None
            },
            "stress_responses": {
                "portfolio_down_10_percent": None,
                "portfolio_down_20_percent": None,
                "portfolio_down_30_percent": None,
                "unexpected_expense": None,
                "job_loss_scenario": None
            },
            "confidence_and_biases": {
                "investment_confidence": None,
                "overconfidence_signs": None,
                "analysis_paralysis": None,
                "confirmation_bias": None,
                "recency_bias": None,
                "home_bias": None
            }
        },
        "lifestyleAndPreferences": {
            "currentLifestyle": {
                "housingType": None,
                "transportationMode": None,
                "socialSpending": None,
                "travelFrequency": None,
                "hobbiesAndInterests": [],
                "healthAndFitness": None
            },
            "futureAspirations": {
                "desiredLifestyle": None,
                "workLifeBalance": None,
                "geographicPreferences": None,
                "careerAmbitions": None,
                "familyPlans": None,
                "retirementVision": None
            },
            "financialPhilosophy": {
                "relationshipWithMoney": None,
                "spendingVsSaving": None,
                "riskComfort": None,
                "wealthDefinition": None
            }
        }
    }

async def extract_profile_from_conversation(conversation_history: List[Dict]) -> Dict[str, Any]:
    """
    Extract structured profile from conversation history using LLM
    """
    try:
        # Convert conversation history to text
        conversation_text = ""
        for msg in conversation_history:
            role = msg.get("role", "")
            if role == "user":
                parts = msg.get("parts", [])
                if parts and "text" in parts[0]:
                    conversation_text += f"User: {parts[0]['text']}\n"
            elif role == "model":
                parts = msg.get("parts", [])
                if parts and "text" in parts[0]:
                    conversation_text += f"Assistant: {parts[0]['text']}\n"
        
        # Load schema
        schema = load_profile_schema()
        
        # Build the extraction prompt
        prompt = PROFILE_EXTRACTION_PROMPT.format(
            profile_schema=json.dumps(schema, indent=2),
            conversation_text=conversation_text
        )
        
        # Query LLM for extraction
        messages = [{"role": "user", "parts": [{"text": prompt}]}]
        result = await query_gemini(messages)
        
        # Parse response
        if result.get('candidates') and result['candidates'][0].get('content'):
            response_text = result['candidates'][0]['content']['parts'][0].get('text', '')
            
            # Try to parse JSON
            try:
                # Clean up the response (remove any markdown formatting)
                json_text = response_text.strip()
                if json_text.startswith('```json'):
                    json_text = json_text[7:]
                if json_text.endswith('```'):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                profile = json.loads(json_text)
                logging.info(f"Successfully extracted profile: {profile}")
                return profile
                
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON from LLM response: {e}")
                logging.error(f"Response was: {response_text}")
                return schema  # Return empty schema as fallback
        
        return schema  # Return empty schema as fallback
        
    except Exception as e:
        logging.error(f"Error in profile extraction: {e}")
        return load_profile_schema()  # Return empty schema as fallback

def validate_profile(profile: Dict[str, Any]) -> bool:
    """
    Validate that the extracted profile has minimum required information
    """
    try:
        # Check for essential fields
        user_profile = profile.get("userProfile", {})
        financial_snapshot = user_profile.get("financialSnapshot", {})
        
        # Must have at least income or some financial info
        has_financial_info = (
            financial_snapshot.get("monthlyIncome") is not None or
            financial_snapshot.get("monthlyExpenses") is not None
        )
        
        # Must have some goals
        goals = profile.get("financialGoals", {})
        has_goals = (
            len(goals.get("shortTerm", [])) > 0 or
            len(goals.get("mediumTerm", [])) > 0 or
            len(goals.get("longTerm", [])) > 0
        )
        
        return has_financial_info or has_goals
        
    except Exception:
        return False

async def get_profile_summary(profile: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the extracted profile
    """
    summary_prompt = f"""
    Create a brief, human-readable summary of this financial profile:
    
    {json.dumps(profile, indent=2)}
    
    Focus on the key aspects: current situation, main goals, and risk profile.
    Keep it under 150 words and write in a friendly, professional tone.
    """
    
    try:
        messages = [{"role": "user", "parts": [{"text": summary_prompt}]}]
        result = await query_gemini(messages)
        
        if result.get('candidates') and result['candidates'][0].get('content'):
            return result['candidates'][0]['content']['parts'][0].get('text', 'Profile summary unavailable.')
    
    except Exception as e:
        logging.error(f"Error generating profile summary: {e}")
    
    return "Profile extracted successfully. Generating recommendations..."