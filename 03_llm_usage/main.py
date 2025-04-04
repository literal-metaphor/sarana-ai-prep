from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from io import BytesIO
import fitz
import logging
import os
from google import genai
from google.genai import types
import dotenv

dotenv.load_dotenv()

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
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    # Define config
    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="Please help me summarize this PDF content and explain it in concise yet clear and explanatory manner:"),
                types.Part.from_text(text=context)
            ]
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        system_instruction="You are an AI summarizer specialized to summarize parsed PDF documents. Parsed documents may contain jumbled mess, incomplete, or incorrect text formatting. But nevertheless, your ability allows you to make sense of it all an explain the summary of the PDF in concise but clear and explanatory manner. The PDF may be presented in different language, but you will still be able to make sense of it and provide a summary in English.",
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="BLOCK_NONE",
            ),
        ],
        response_mime_type="text/plain",
        temperature=0.2,
        top_p=0.9
    )
    
    def stream_response():
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                yield chunk.text
                
    return stream_response()