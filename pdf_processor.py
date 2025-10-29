import pypdf
import io

def simple_text_splitter(text, chunk_size=1500, chunk_overlap=200):
    """A basic function to split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        
        start += chunk_size - chunk_overlap
    return chunks

def extract_text_from_pdf(pdf_bytes):
    """Extracts all text from a PDF given as bytes."""
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() or ""
        return full_text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""