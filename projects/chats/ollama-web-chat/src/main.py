import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Ollama Server config
OLLAMA_HOST = "192.168.1.62"
OLLAMA_PORT = 11434
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.clients_context = {}  # websocket -> context list

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.clients_context[websocket] = []

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.clients_context:
            del self.clients_context[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get(request: Request):
    # For simplicity, let's assume these are some available models from Ollama or preset
    available_models = [
        "llama2", "gpt4all", "vicuna", "llama2-7b", "ollama-test"
    ]
    return templates.TemplateResponse("index.html", {"request": request, "models": available_models})


async def query_ollama(model: str, messages: List[dict]) -> str:
    """
    Send chat messages to Ollama HTTP API for the given model, returns the model's reply.
    The Ollama API expects messages as [{"role": "user"|"assistant"|"system", "content": "text"}, ...]
    """
    url = f"{OLLAMA_BASE_URL}/chat/{model}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "messages": messages
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            json_resp = resp.json()
            # The response from Ollama is expected to have "choices" in the form:
            # {"choices": [{"message": {"role": "assistant","content": "response text"}}]}
            if "choices" in json_resp and len(json_resp["choices"]) > 0:
                return json_resp["choices"][0]["message"]["content"]
            else:
                return "[No response from model]"
        else:
            return f"[Error querying Ollama: {resp.status_code} - {resp.text}]"


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # We expect the first message from client to initialize the chat model and optionally system prompt
    try:
        init_data_json = await websocket.receive_text()
        init_data = json.loads(init_data_json)
        model = init_data.get("model", "llama2")
        system_prompt = init_data.get("system_prompt", "You are a helpful assistant.")
        # context messages list
        context_messages = [{"role": "system", "content": system_prompt}]
        manager.clients_context[websocket] = context_messages

        await manager.send_personal_message(json.dumps({"type": "status", "msg": f"Connected to model {model}"}), websocket)

        while True:
            data = await websocket.receive_text()
            client_msg = json.loads(data)
            # Expect: {"type":"user_message", "content":"hello"}
            if client_msg.get("type") == "user_message":
                user_text = client_msg.get("content", "")
                if not user_text.strip():
                    continue
                # Append user's message to context
                context_messages.append({"role": "user", "content": user_text})
                await manager.send_personal_message(json.dumps({"type": "user_message", "content": user_text}), websocket)

                try:
                    # Query Ollama with the current context
                    assistant_reply = await query_ollama(model=model, messages=context_messages)
                    # Append assistant message to context
                    context_messages.append({"role": "assistant", "content": assistant_reply})
                    # Send assistant reply to client
                    await manager.send_personal_message(json.dumps({"type": "assistant_message", "content": assistant_reply}), websocket)
                except Exception as e:
                    err_msg = f"[Error querying model: {str(e)}]"
                    await manager.send_personal_message(json.dumps({"type": "assistant_message", "content": err_msg}), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

