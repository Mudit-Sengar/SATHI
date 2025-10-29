import os
import glob
import qdrant_client

# Import functions from our other files
from config import QDRANT_COLLECTION
from ollama_client import get_ollama_embedding
from pdf_processor import simple_text_splitter, extract_text_from_pdf
from qdrant_manager import get_qdrant_client, upsert_chunks

# --- Configuration ---
DATA_FOLDER = "./data"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 250

def main():
    """
    Main ingestion function.
    1. Finds all PDFs in DATA_FOLDER.
    2. Extracts text, splits into chunks.
    3. Gets embedding for the first chunk to determine vector size.
    4. Re-creates the Qdrant collection (wiping old data).
    5. Embeds and upserts all chunks into Qdrant.
    """
    print("Starting ingestion process...")
    
    # --- 1. Find all PDFs ---
    pdf_files = glob.glob(os.path.join(DATA_FOLDER, "*.pdf"))
    if not pdf_files:
        print(f"Error: No PDF files found in '{DATA_FOLDER}' folder.")
        print("Please create the 'data' folder and add your PDFs.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process.")

    all_chunks = []
    
    # --- 2. Extract text and split into chunks ---
    for pdf_file in pdf_files:
        print(f"  - Processing {os.path.basename(pdf_file)}...")
        try:
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()
            
            full_text = extract_text_from_pdf(pdf_bytes)
            if not full_text.strip():
                print(f"    Warning: No text extracted from {os.path.basename(pdf_file)}.")
                continue
                
            chunks = simple_text_splitter(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
            all_chunks.extend(chunks)
            print(f"    Extracted {len(chunks)} chunks.")
            
        except Exception as e:
            print(f"    Error processing {os.path.basename(pdf_file)}: {e}")
            
    if not all_chunks:
        print("Error: No text chunks were extracted from any PDF. Aborting.")
        return

    print(f"\nTotal chunks to index: {len(all_chunks)}")

    # --- 3. Get embedding for the first chunk (to get vector size) ---
    print("Connecting to Ollama to get embedding dimension...")
    try:
        sample_embedding = get_ollama_embedding(all_chunks[0])
        if sample_embedding is None:
            print("Error: Could not connect to Ollama or get embedding.")
            print("Please ensure Ollama is running.")
            return
        
        vector_size = len(sample_embedding)
        print(f"Ollama embedding dimension: {vector_size}")
        
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return

    # --- 4. Get Qdrant client and re-create collection ---
    client = get_qdrant_client()
    
    print(f"Re-creating Qdrant collection: '{QDRANT_COLLECTION}'")
    try:
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qdrant_client.http.models.VectorParams(
                size=vector_size,
                distance=qdrant_client.http.models.Distance.COSINE
            )
        )
        print("Collection re-created successfully.")
    except Exception as e:
        print(f"Error re-creating Qdrant collection: {e}")
        return

    # --- 5. Embed and upsert all chunks ---
    print(f"Embedding and upserting {len(all_chunks)} chunks into Qdrant...")
    
    indexed_count = upsert_chunks(client, all_chunks)
    
    if indexed_count > 0:
        print(f"\nSuccessfully indexed {indexed_count} chunks!")
    else:
        print("\nWarning: No chunks were indexed. Check Ollama connection.")
        
    print("Ingestion process complete.")


if __name__ == "__main__":
    main()