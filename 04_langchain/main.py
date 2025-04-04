from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from io import BytesIO
import fitz
import logging
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/")
async def uploadPdf(file: UploadFile = File(...)):
    # Only allow PDF
    if file.filename.split('.')[-1].lower() != 'pdf':
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Read the PDF file and parse the content
    pdf_document = fitz.open(stream=BytesIO(await file.read()), filetype="pdf")
    context = ''
    for page in pdf_document:
        context += page.get_text()
    pdf_document.close()

    # Stream the AI response
    return StreamingResponse(
        generate(context),
        media_type="text/event-stream"
    )

def generate(context: str):
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI summarizer specialized to summarize parsed PDF documents. Parsed documents may contain jumbled mess, incomplete, or incorrect text formatting. But nevertheless, your ability allows you to make sense of it all an explain the summary of the PDF in concise but clear and explanatory manner. The PDF may be presented in different language, but you will still be able to make sense of it and provide a summary in English."),
        ("user", "Please help me summarize this PDF content and explain it in concise yet clear and explanatory manner:"),
        ("user", "{context}"),
    ])

    chain = prompt | llm

    def stream_response():
        for chunk in chain.stream({"context": context}):
            yield chunk.content

    return stream_response()