import os
from typing import Annotated, List
import json
import uuid

from fastapi import FastAPI, Cookie, Response
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
    max_output_tokens=None,
    top_p=0.9,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }
)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.set_entry_point("chatbot")
graph_builder.set_finish_point("chatbot")
graph = graph_builder.compile()

def load_session_history(session_id: str):
    try:
        with open("sessions.json", "r") as f:
            sessions = json.load(f)
            return next((session["messages"] for session in sessions if session["id"] == session_id), [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_session_history(session_id: str, messages: List[dict]):
    try:
        with open("sessions.json", "r+") as f:
            try:
                sessions = json.load(f)
            except json.JSONDecodeError:
                sessions = []
            session_exists = False
            for session in sessions:
                if session["id"] == session_id:
                    session["messages"] = messages
                    session_exists = True
                    break
            if not session_exists:
                sessions.append({"id": session_id, "messages": messages})
            f.seek(0)
            json.dump(sessions, f, indent=4)
            f.truncate()
    except FileNotFoundError:
        with open("sessions.json", "w") as f:
            json.dump([{"id": session_id, "messages": messages}], f, indent=4)

async def generate_response(messages: List[dict]):
    initial_state = {"messages": messages}
    for event in graph.stream(initial_state):
        for value in event.values():
            response = value["messages"][-1].content
            yield f"data: {response}\n\n"
            messages.append({"role": "assistant", "content": response})

@app.post("/")
async def chat(request: dict, response: Response, langgraph_session: str = Cookie(None)):
    messages = request.get("messages", [])
    if not langgraph_session:
        langgraph_session = str(uuid.uuid4())
    history = load_session_history(langgraph_session)
    combined_messages = history + messages
    
    async def generate_response_wrapper():
        async for chunk in generate_response(combined_messages):
            yield chunk
        new_messages = combined_messages.copy()
        for message in messages:
            new_messages.append({"role": "assistant", "content": message["content"]})
        save_session_history(langgraph_session, new_messages)

    response = StreamingResponse(generate_response_wrapper(), media_type="text/event-stream")
    response.set_cookie("langgraph_session", langgraph_session)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
