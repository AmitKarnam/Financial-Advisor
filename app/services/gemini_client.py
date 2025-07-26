import os
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

headers = {
    "Content-Type": "application/json",
}

async def query_gemini(messages):
    payload = {
        "contents": messages
    }
    async with httpx.AsyncClient(timeout=60) as client:  # Increase timeout to 60 seconds
        response = await client.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", headers=headers, json=payload)
        return response.json()
