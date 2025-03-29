from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from io import BytesIO
import fitz
import logging
import tempfile

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# TODO: Basic content extraction, might need better method
@app.post("/")
async def uploadPdf(file: UploadFile = File(...)):
    # Only allow PDF
    if file.filename.split('.')[-1].lower() != 'pdf':
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Read the PDF file and parse the content
    pdf_document = fitz.open(stream=BytesIO(await file.read()), filetype="pdf")
    md = ''
    for page in pdf_document:
        md += page.get_text()
    pdf_document.close()
    
    # Write the content to a temporary file and return download response
    md_file = file.filename.replace('.pdf', '.md')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as temp_file:
        temp_file.write(md.encode('utf-8'))
        return FileResponse(path=temp_file.name, media_type="text/markdown", filename=md_file)
    
    raise HTTPException(status_code=500, detail="Failed to process file")