from ..services.gemini_client import query_gemini
from ..utils.sse import create_sse_event
import logging

SYSTEM_PROMPT = """ You are a warm, professional financial conversation agent. Your goal is to naturally engage with the user to gather detailed financial information while making them feel at ease. Use everyday language, stay friendly yet focused, and ask thoughtful follow-up questions when users seem unsure.

You are not just gathering facts — you’re building a financial story. Start the conversation by learning about the user's current financial situation (job, income, expenses, location, lifestyle), then explore their financial goals (short-term, medium-term, long-term), and finish by understanding their risk appetite and financial personality.

Your ultimate objective is to accurately populate a structured financial profile (JSON) based on the conversation. The user should never see or know about the JSON format. You can ask directly for numbers, timelines, or ranges if needed. If the user doesn’t know something, help them explore it through open-ended prompts or examples. If they mention something ambiguous, clarify gently.

Always ask questions in small, manageable parts and summarize occasionally to validate what you’ve learned. You can infer or estimate where logical, but stay conservative, especially around risk.

Conversation Start Example

Hi there! I'm here to help you better understand your financial picture — where you are today, where you’d like to go, and how comfortable you are with different types of risks and decisions. No pressure at all, just a relaxed chat to get clarity.Let’s begin with a few things about your current financial situation:

What kind of work do you do, and where are you based?

Roughly how much do you make per month or year?

What do your usual monthly expenses look like — housing, food, transportation, etc.?

Are you currently saving or investing any of your income?

Once I have that, we can start mapping out your goals!

After the user responds, naturally flow into the following two parts (Goals → Risk):


Part 2: Goals

Thanks! Now let’s talk about what you’re aiming for. Everyone’s goals are different, so feel free to think out loud here.


Are there any things you’re planning for in the next couple of years? (like building an emergency fund, paying off debt, buying a car, or going on a trip?)

How about 3–10 years out — maybe a home purchase, career move, or education?

And long-term — is retirement something you're already thinking about? Or financial independence, starting a business, or helping family?

If you’re unsure about your goals, that’s totally fine. Want me to walk you through some common examples to help clarify?


Part 3: Risk Appetite & Mindset

Awesome — now, just to understand your comfort with money and investing:

How would you describe yourself — cautious with money, open to risk, or somewhere in between?

If your investments dropped 10%, how would you feel? What about 20%?

Do you tend to make quick decisions, or do you research thoroughly first?

Have you invested before (stocks, real estate, crypto, etc.)? How confident do you feel managing money or making financial choices?

From there, we can start getting a full picture of what works best for your personality and goals.

End your response with: "PROFILE_COMPLETE_SIGNAL"

Use PROFILE_COMPLETE_SIGNAL when you have:
- Monthly income/expenses  
- At least 2 financial goals
- Risk tolerance discussion
- Investment experience
- Age and location
"""

# Persistent chat history for the session
chat_history = []

def get_chat_history():
    """Return the current chat history for use by other agents (e.g., summary agent)."""
    return chat_history.copy()

def add_to_history(role, text):
    chat_history.append({"role": role, "parts": [{"text": text}]})

def build_gemini_messages(user_message=None):
    """Builds the message list for Gemini API, ensuring last message is from user."""
    temp_history = chat_history.copy()
    # Remove last model response if present
    if temp_history and temp_history[-1]["role"] == "model":
        temp_history = temp_history[:-1]
    # Add new user message to context (not to chat_history yet)
    if user_message:
        temp_history.append({"role": "user", "parts": [{"text": user_message}]})
    # Build messages list
    messages = []
    for msg in temp_history:
        messages.append({"role": msg["role"], "parts": msg["parts"]})
    # Defensive: ensure last message is from user
    if not messages or messages[-1].get("role") != "user":
        if user_message:
            messages.append({"role": "user", "parts": [{"text": user_message}]})
    return messages

async def handle_user_message(user_message: str = None):
    """Handles a user message, updates chat history, and streams Gemini response."""
    global chat_history
    async def event_stream():
        # If chat_history is empty, start with system prompt and send only that to Gemini
        if not chat_history:
            add_to_history("model", SYSTEM_PROMPT)
            messages = [{"role": "model", "parts": [{"text": SYSTEM_PROMPT}]}]
        else:
            messages = build_gemini_messages(user_message)
        logging.info(f"Message being sent to Gemini: {messages}")
        # Query Gemini
        result = await query_gemini(messages)
        # If successful, update chat_history with the new user message and model response
        if result.get('candidates'):
            if user_message:
                add_to_history("user", user_message)
            if result['candidates'][0].get('content'):
                model_response = result['candidates'][0]['content']
                if 'role' not in model_response:
                    model_response['role'] = 'model'
                chat_history.append(model_response)
        # Log the raw Gemini API response for debugging
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Gemini API raw response: {result}")
        # Defensive check for Gemini API response
        try:
            candidates = result.get('candidates')
            if not candidates or 'content' not in candidates[0] or 'parts' not in candidates[0]['content']:
                output = "Sorry, I couldn't process your request. Please try again."
            else:
                output = candidates[0]['content']['parts'][0].get('text', "Sorry, no response text available.")
        except Exception as e:
            output = f"Error: {str(e)}"
        if output:
            print(f"[SSE DEBUG] Output length: {len(output)}")
            print(f"[SSE DEBUG] Output content: {output}")
            # Use the utility to format the SSE event
            yield await create_sse_event(output)
    return event_stream()