from services.gemini_client import query_gemini

SUMMARY_PROMPT = """
Summarise the following conversation into the following JSON structure:
{
  "userProfile": {
    "demographics": {
      "currentAge": null,
      "targetRetirementAge": null,
      "maritalStatus": null,
      "dependents": null,
      "location": null
    },
    "financialSnapshot": {
      "monthlyIncome": null,
      "monthlyExpenses": null,
      "currentSavingsRate": null,
      "expectedIncomeGrowthRate": null,
      "jobStability": null
    },
    "investmentProfile": {
      "riskTolerance": null,
      "investmentExperience": null,
      "investmentKnowledge": null,
      "preferredInvestmentTypes": [],
      "investmentTimeHorizon": null
    },
    "behavioralTraits": {
      "savingsDiscipline": null,
      "spendingPattern": null,
      "financialGoalClarity": null,
      "moneyMotivation": null
    }
  },
  "financialGoals": {
    "shortTerm": [
      {
        "goalName": null,
        "targetAmount": null,
        "currentAmount": null,
        "timeline": null,
        "priority": null,
        "monthlySavingsRequired": null,
        "goalType": null,
        "description": null,
        "flexibility": null
      }
    ],
    "mediumTerm": [
      {
        "goalName": null,
        "targetAmount": null,
        "currentAmount": null,
        "timeline": null,
        "priority": null,
        "monthlySavingsRequired": null,
        "goalType": null,
        "description": null,
        "flexibility": null,
        "impactOnCareer": null
      }
    ],
    "longTerm": [
      {
        "goalName": null,
        "targetAmount": null,
        "currentAmount": null,
        "timeline": null,
        "priority": null,
        "monthlySavingsRequired": null,
        "goalType": null,
        "description": null,
        "flexibility": null,
        "legacyImportance": null
      }
    ]
  },
  "riskAppetite": {
    "risk_appetite_indicators": {
      "risk_tolerance_score": null,
      "risk_capacity_score": null,
      "loss_tolerance_percentage": null,
      "recovery_time_comfort": null,
      "volatility_comfort": null,
      "sleep_at_night_threshold": null
    },
    "market_behavior_patterns": {
      "bear_market_response": null,
      "bull_market_response": null,
      "market_crash_history": null,
      "fomo_susceptibility": null,
      "panic_selling_tendency": null,
      "market_timing_attempts": null
    },
    "financial_psychology": {
      "money_relationship": null,
      "biggest_financial_fear": null,
      "motivating_financial_goal": null,
      "decision_making_under_pressure": null,
      "regret_aversion": null,
      "optimism_bias": null,
      "anchoring_tendency": null
    },
    "experience_and_knowledge": {
      "years_investing": null,
      "investment_knowledge_level": null,
      "past_major_losses": null,
      "recovery_from_losses": null,
      "learning_from_mistakes": null,
      "financial_education": null
    },
    "behavioral_traits": {
      "planning_horizon": null,
      "research_depth": null,
      "herd_mentality": null,
      "patience_level": null,
      "discipline_score": null,
      "emotional_control": null,
      "diversification_understanding": null
    },
    "life_context": {
      "age": null,
      "income_stability": null,
      "dependents": null,
      "major_expenses_timeline": null,
      "career_stage": null,
      "health_status": null,
      "insurance_coverage": null
    },
    "stress_responses": {
      "portfolio_down_10_percent": null,
      "portfolio_down_20_percent": null,
      "portfolio_down_30_percent": null,
      "unexpected_expense": null,
      "job_loss_scenario": null
    },
    "confidence_and_biases": {
      "investment_confidence": null,
      "overconfidence_signs": null,
      "analysis_paralysis": null,
      "confirmation_bias": null,
      "recency_bias": null,
      "home_bias": null
    }
  },
  "lifestyleAndPreferences": {
    "currentLifestyle": {
      "housingType": null,
      "transportationMode": null,
      "socialSpending": null,
      "travelFrequency": null,
      "hobbiesAndInterests": [],
      "healthAndFitness": null
    },
    "futureAspirations": {
      "desiredLifestyle": null,
      "workLifeBalance": null,
      "geographicPreferences": null,
      "careerAmbitions": null,
      "familyPlans": null,
      "retirementVision": null
    },
    "financialPhilosophy": {
      "relationshipWithMoney": null,
      "spendingVsSaving": null,
      "riskComfort": null,
      "wealthDefinition": null
    }
  }
}

"""

async def summarise_conversation(chat_history: list):
    messages = [
        {"role": "model", "parts": [SUMMARY_PROMPT]},
        {"role": "user", "parts": ["\n".join(chat_history)]}
    ]
    result = await query_gemini(messages)
    return result['candidates'][0]['content']['parts'][0]['text']
