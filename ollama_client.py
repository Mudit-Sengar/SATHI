import requests
import json
import streamlit as st
from config import OLLAMA_URL, OLLAMA_EMBED_MODEL, OLLAMA_CHAT_MODEL

def get_ollama_embedding(text, model=OLLAMA_EMBED_MODEL):
    """
    Gets vector embeddings for a text snippet from the Ollama API.
    """
    try:
        url = f"{OLLAMA_URL}/api/embeddings"
        payload = {"model": model, "prompt": text}
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()["embedding"]
    
    except requests.exceptions.ConnectionError:
        print(f"ConnectionError: Could not connect to Ollama at {OLLAMA_URL}. Is Ollama running?")
        return None
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def query_llama3(prompt, model=OLLAMA_CHAT_MODEL):
    """
    Sends a prompt to the Llama 3 model via the Ollama API and streams the response.
    (This is only used by app.py, so st.error is fine here)
    """
    try:
        url = f"{OLLAMA_URL}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()

        # Create a generator to yield each response chunk
        def response_generator():
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        json_chunk = json.loads(chunk.decode('utf-8'))
                        
                        if json_chunk.get('done', False):
                            break
                        
                        if 'response' in json_chunk:
                            yield json_chunk['response']

                    except json.JSONDecodeError:
                        st.warning(f"Failed to decode JSON chunk: {chunk}")
        
        return response_generator()

    except requests.exceptions.ConnectionError:
        st.error(f"ConnectionError: Could not connect to Ollama at {OLLAMA_URL}. Is Ollama running?")
        return iter(["**Error:** Could not connect to Ollama."])
    except Exception as e:
        st.error(f"Error querying Llama3: {e}")
        return iter([f"**Error:** {e}"])