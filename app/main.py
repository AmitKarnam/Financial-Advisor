from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from app.agents.conversations import handle_user_message
from app.utils.sse import create_sse_event
import os

app = FastAPI()

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body.get("message")
    stream = await handle_user_message(user_input)
    return StreamingResponse(stream, media_type="text/event-stream")

@app.get("/chat")
async def get_initial_message():
    # Get initial message without user input
    stream = await handle_user_message()
    return StreamingResponse(stream, media_type="text/event-stream")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))
