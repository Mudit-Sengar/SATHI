import streamlit as st
import os

def load_faqs(filepath="faqs.txt"):
    """
    Loads FAQs from a text file.
    Expected format:
    Question
    Answer
    ===
    """
    faqs = {}
    if not os.path.exists(filepath):
        st.warning(f"FAQ file not found: {filepath}")
        return faqs

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.split('===')
        for block in blocks:
            if not block.strip():
                continue
            
            # Split only on the first newline to separate question from answer
            parts = block.strip().split('\n', 1) 
            if len(parts) == 2:
                question = parts[0].strip().lower() # Store question in lowercase for matching
                answer = parts[1].strip()
                if question:
                    faqs[question] = answer
            
    except Exception as e:
        st.error(f"Error loading FAQs: {e}")
    
    return faqs