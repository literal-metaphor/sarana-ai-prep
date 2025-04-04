# from fastapi import FastAPI, HTTPException
# from fastapi.responses import StreamingResponse
# import logging
# import os
# from dotenv import load_dotenv

# from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
# from langchain_core.prompts import ChatPromptTemplate

# load_dotenv()

# # Set up logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# app = FastAPI()

# @app.get("/")
# async def chatbot():
#     # TODO: 

#     # Stream the AI response
#     return StreamingResponse(
#         generate(context),
#         media_type="text/event-stream"
#     )

# def generate(context: str):
#     llm = ChatGoogleGenerativeAI(
#         model="gemini-2.0-flash",
#         google_api_key=os.getenv("GEMINI_API_KEY"),
#         temperature=0.2,
#         max_output_tokens=None,
#         top_p=0.9,
#         safety_settings = {
#             HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
#         }
#     )

#     prompt = ChatPromptTemplate.from_messages([
#         ("system", "You are an AI summarizer specialized to summarize parsed PDF documents. Parsed documents may contain jumbled mess, incomplete, or incorrect text formatting. But nevertheless, your ability allows you to make sense of it all an explain the summary of the PDF in concise but clear and explanatory manner. The PDF may be presented in different language, but you will still be able to make sense of it and provide a summary in English."),
#         ("user", "Please help me summarize this PDF content and explain it in concise yet clear and explanatory manner:"),
#         ("user", "{context}"),
#     ])

#     chain = prompt | llm

#     def stream_response():
#         for chunk in chain.stream({"context": context}):
#             yield chunk.content

#     return stream_response()

import os
from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
# from langgraph.checkpoint.memory import MemorySaver
# memory = MemorySaver()

from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
    max_output_tokens=None,
    top_p=0.9,
    safety_settings = {
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

def run_interactive_chatbot():
    messages = []
    while True:
        user_input = input("User: ")

        messages.append(HumanMessage(content=user_input))
        initial_state = {"messages": messages}
        
        for event in graph.stream(initial_state):
            for value in event.values():
                response = value["messages"][-1].content
                print("Assistant:", response)
                messages.append(AIMessage(content=response))

if __name__ == "__main__":
    run_interactive_chatbot()