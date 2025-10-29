import streamlit as st

from config import QDRANT_COLLECTION
from ollama_client import get_ollama_embedding, query_llama3
from qdrant_manager import get_qdrant_client, search_qdrant
from faq_loader import load_faqs  # Import the FAQ loader


st.set_page_config(page_title="SATHI", page_icon="🌱")

logo_url = "./media/sathi-portal.png"


st.logo(logo_url, size='large')

st.title("SATHI - Your Seed Assistant")

# --- Initialize Qdrant and FAQs in session state ---
if "qdrant_client" not in st.session_state:
    try:
        st.session_state.qdrant_client = get_qdrant_client()
        try:
            st.session_state.qdrant_client.get_collection(collection_name=QDRANT_COLLECTION)
            st.session_state.qdrant_ready = True
            st.info("Hi, how can I help you? The document store is ready.")
        except Exception as e:
            st.session_state.qdrant_ready = False
            st.error(f"Vector store '{QDRANT_COLLECTION}' not found.")
            st.error("Please run the `ingest.py` script first to build the database.")
            st.stop()

    except Exception as e:
        st.error(f"Failed to initialize Qdrant client: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Load FAQs from file once
if "faqs" not in st.session_state:
    st.session_state.faqs = load_faqs("faqs.txt")

# --- Chat Interface ---

# Display existing chat history (user + assistant)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle new user input ---
if prompt := st.chat_input("Enter your question..."):
    # Add user message to chat history and show it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Assistant Response Block ---
    assistant_placeholder = st.chat_message("assistant")
    with assistant_placeholder:
        response_placeholder = st.empty()
        response_text = ""

        # 1. Check FAQs first
        faq_answer = st.session_state.faqs.get(prompt.lower().strip())

        if faq_answer:
            response_text = faq_answer
            response_placeholder.markdown(response_text)

        # 2. If not in FAQ, go through RAG pipeline
        elif not st.session_state.qdrant_ready:
            response_text = "The vector store is not ready. Please contact the administrator."
            response_placeholder.warning(response_text)

        else:
            with st.spinner("Thinking..."):
                # a. Get embedding
                query_embedding = get_ollama_embedding(prompt)

                if query_embedding:
                    # b. Search for context
                    context = search_qdrant(st.session_state.qdrant_client, query_embedding)

                    if not context:
                        rag_prompt = (
                            f"User Question: {prompt}\n\n"
                            "Note: I could not find any relevant information in the uploaded documents to answer this question."
                        )
                    else:
                        rag_prompt = f"""
                        You are a helpful assistant. Use the following context from a document to answer the user's question.
                        If the answer is not found in the context, say "I could not find the answer in the document."
                        Do not make up information. Ask the user to ask relevant questions.

                        Context:
                        {context}

                        User Question:
                        {prompt}

                        Answer:
                        """

                    # c. Query Llama 3 and stream response
                    full_response = ""
                    for chunk in query_llama3(rag_prompt):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")

                    response_placeholder.markdown(full_response)
                    response_text = full_response
                else:
                    response_text = "Error: Could not get embedding for your query. Please check the Ollama connection."
                    response_placeholder.error(response_text)

    # --- Save Assistant Response to History (only once) ---
    if response_text:
        st.session_state.messages.append({"role": "assistant", "content": response_text})
