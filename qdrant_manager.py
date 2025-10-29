import qdrant_client
import streamlit as st
import uuid
from config import QDRANT_COLLECTION
from ollama_client import get_ollama_embedding
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_qdrant_client():
    """Initializes and returns a persistent, local Qdrant client."""
    
    return qdrant_client.QdrantClient(host="localhost", port = 6333)

def upsert_chunks(client, chunks, batch_size=128, max_workers=10):
    """
    Embeds chunks in parallel and upserts them into Qdrant in batches.
    
    :param client: The Qdrant client instance.
    :param chunks: A list of text chunks to embed and index.
    :param batch_size: The number of points to upsert to Qdrant at a time.
    :param max_workers: The number of parallel threads to use for embedding.
    """
    points_to_upsert = []
    total_indexed = 0
    total = len(chunks)
    
    print(f"Starting parallel embedding of {total} chunks with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        future_to_chunk = {
            executor.submit(get_ollama_embedding, chunk): chunk 
            for chunk in chunks
        }
        
        processed_count = 0
        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            processed_count += 1
            
            try:
                embedding = future.result()
                
                if embedding:
                    points_to_upsert.append(
                        qdrant_client.http.models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=embedding,
                            payload={"text": chunk}
                        )
                    )
                else:
                    print(f"  Warning: Failed to get embedding for a chunk.")
                
                if len(points_to_upsert) >= batch_size or processed_count == total:
                    if points_to_upsert:
                        print(f"  ... upserting batch of {len(points_to_upsert)} points...")
                        client.upsert(
                            collection_name=QDRANT_COLLECTION,
                            points=points_to_upsert,
                            wait=True
                        )
                        total_indexed += len(points_to_upsert)
                        points_to_upsert = []
            
            except Exception as e:
                print(f"  Error processing chunk: {e}")
            
            # Progress indicator
            if processed_count % (total // 10 or 1) == 0 or processed_count == total:
                 print(f"  ... embedding progress: {processed_count}/{total} chunks processed.")

    return total_indexed

def search_qdrant(client, query_embedding, top_k=3):
    """Searches Qdrant for the top_k most similar vectors."""
    try:
        search_results = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=top_k
        )
        
        context = ""
        if search_results:
            context = "\n\n---\n\n".join([
                result.payload["text"] for result in search_results
            ])
        return context
    except Exception as e:
        st.error(f"Error searching Qdrant: {e}")
        return ""