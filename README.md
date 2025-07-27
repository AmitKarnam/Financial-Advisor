# Financial-Advisor

**Financial-Advisor** is an AI-powered web application that provides personalized financial guidance and investment recommendations through a conversational interface. The project leverages multi-agent orchestration, structured user profiling, and real-time chat to deliver tailored advice based on the user's financial situation, goals, and personality.

## Use Case

This application is designed for individuals seeking personalized investment advice and financial planning in an interactive, user-friendly manner. By simulating a conversation with a virtual financial advisor, users can:

- **Share their financial background and goals** in natural language.
- **Receive structured financial profiles** distilled from the conversation.
- **Get actionable, personalized investment recommendations** based on their unique context, preferences, and risk appetite.
- **Engage in follow-up Q&A** to clarify recommendations or explore further financial topics.

## Key Features

- **Conversational Chat UI:** Natural language interaction for easy profile collection and advice delivery.
- **Multi-Agent Workflow:** Orchestration of three specialized agents—conversation, profile summarization, and recommendation.
- **Structured Financial Profiling:** Extracts detailed financial, behavioral, and lifestyle attributes into a comprehensive JSON profile.
- **Personalized Recommendations:** Leverages user profile and external data (e.g., MCP) to suggest investment strategies.
- **Real-Time Responses:** Uses Server-Sent Events (SSE) for streaming advice and status updates.

---

## Architecture Overview

The architecture is built around a modular, multi-agent pipeline orchestrated by FastAPI backend and a responsive frontend.

### 1. **Frontend (`app/index.html`)**

- **Chat Container:** Renders user and agent messages, styled for readability and accessibility.
- **Input Handling:** Accepts user input, triggers chat requests, and manages UI state (loading, error, etc.).
- **Formatting Engine:** Translates markdown-like text (bold, lists, paragraphs) from backend to HTML for display.
- **Event Streaming:** Uses JavaScript EventSource to receive live updates from the backend.

### 2. **Backend (Python, FastAPI)**

#### Main Endpoints (`app/main.py`)

- `/chat` (POST): Orchestrates the multi-agent workflow for each user message.
- `/chat` (GET): Delivers the initial system prompt to start the conversation.
- `/profile`: Returns the structured profile extracted from conversation.
- `/recommendations`: Provides personalized investment recommendations.
- `/reset`: Resets the chat and workflow.
- `/health`: Monitors agent status for reliability.

#### Multi-Agent Orchestration

**AgentCoordinator** (`app/agents/coordinator.py`):
- Manages workflow stages: conversation → profile extraction → recommendations.
- Streams responses to frontend, transitions between workflow stages, and stores chat history.

**Agents:**
- **Conversational Agent** (`app/agents/conversations.py`): Engages with user using a warm, professional tone. Gathers detailed financial data using open-ended, empathetic questions.
- **Summary Agent** (`app/agents/summary.py`): Extracts and organizes the user's financial profile into a highly structured JSON schema covering demographics, financial goals, investment traits, behavioral patterns, lifestyle, and more.
- **Recommendation Agent**: Processes the profile and generates actionable investment advice using external market data (e.g., MCP).

#### Profile Schema Example (`app/agents/summary.py`)

The extracted profile includes:

- **Demographics:** Age, marital status, dependents, location.
- **Financial Snapshot:** Income, expenses, savings rate, job stability.
- **Investment Profile:** Risk tolerance, experience, knowledge, preferred types, time horizon.
- **Behavioral Traits:** Discipline, spending pattern, motivation, goal clarity.
- **Goals & Aspirations:** Short, medium, and long-term objectives.
- **Lifestyle & Preferences:** Housing, transportation, hobbies, geographic preferences.
- **Psychological Dimensions:** Risk comfort, bias detection, stress responses.

#### Orchestration Flow

1. **Start of Conversation:** User greeted, initial questions asked.
2. **Profile Collection:** Conversational agent gathers info through chat.
3. **Profile Summarization:** Summary agent distills info into JSON profile.
4. **Recommendation Generation:** Advice agent uses the profile to suggest investments.
5. **Streaming to Frontend:** All stages stream progress and results to user.

---

## Getting Started

### Prerequisites

- Python 3.8+
- FastAPI

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/AmitKarnam/Financial-Advisor.git
   cd Financial-Advisor
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # (if frontend is built separately)
   ```

### Running the App

```bash
cd app
uvicorn main:app --reload
```
- Visit `http://localhost:8000/` to use the chat-based financial advisor.

---
