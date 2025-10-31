# Copyright (c) 2025 Avnish Kumar
# Licensed under the MIT License.
# See LICENSE file in the project root for details.

import streamlit as st
import os
from PyPDF2 import PdfReader
from transformers import pipeline

# ======================================
# 🚀 Optimized Q&A App (with caching)
# ======================================

# Cached function to extract text once
@st.cache_data
def extract_text_from_pdf(pdf_folder):
    all_text = ""
    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            reader = PdfReader(os.path.join(pdf_folder, file))
            for page in reader.pages:
                all_text += page.extract_text() or ""
    return all_text

# Cached model load
@st.cache_resource
def load_qa_model():
    return pipeline(
        "question-answering",
        model="bert-large-uncased-whole-word-masking-finetuned-squad",
        tokenizer="bert-large-uncased-whole-word-masking-finetuned-squad",
        framework="pt"
    )

# QA helper
def get_best_answer(question, text, qa_pipeline, chunk_size=4000):
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    best_answer = None
    best_score = 0

    for chunk in chunks:
        result = qa_pipeline(question=question, context=chunk)
        if result['score'] > best_score:
            best_score = result['score']
            best_answer = result['answer']
    return best_answer

def split_compound_question(question: str):
    """
    Detects compound 'and' questions like 'When and where ...'
    and splits them into sub-questions.
    Returns a list of sub-questions.
    """
    q = question.lower().strip()

    # Common factual words to check for splitting
    q_types = ["when", "where", "who", "what", "which", "how", "why"]

    # Find multiple wh-words joined by 'and'
    parts = []
    for qt in q_types:
        if f"{qt} and" in q:
            before_and, after_and = q.split("and", 1)
            first_qword = next((w for w in q_types if w in before_and.split()), None)
            second_qword = next((w for w in q_types if w in after_and.split()), None)

            if first_qword and second_qword:
                core = q.replace("?", "").strip()
                # Example: "when and where did he born"
                subject = core.split(second_qword, 1)[-1].strip()
                parts.append(f"{first_qword} {subject}?")
                parts.append(f"{second_qword} {subject}?")
                return parts

    # No compound pattern detected
    return [question]


def smart_answer(question, text, qa_pipeline):
    sub_questions = split_compound_question(question)
    if len(sub_questions) == 1:
        return get_best_answer(sub_questions[0], text, qa_pipeline)

    # Combine answers from sub-questions
    answers = []
    for q in sub_questions:
        ans = get_best_answer(q, text, qa_pipeline)
        answers.append((q, ans))

    # Build a natural combined sentence
    if len(answers) == 2:
        return f"{answers[0][1].capitalize()} in {answers[1][1]}."
    else:
        return " ".join(a[1] for a in answers if a[1])


# ======================================
# Streamlit UI
# ======================================
st.set_page_config(page_title="PDF Q&A", page_icon="📘")

st.title("📚 PDF Question Answering App")

pdf_folder = "docs"  # Example folder name in your project
with st.spinner("📂 Extracting text (only first time)..."):
    all_text = extract_text_from_pdf(pdf_folder)

with st.spinner("🧠 Loading model (only once)..."):
    qa_pipeline = load_qa_model()

# Input
question = st.text_input("Ask your question:", placeholder="e.g., Ask Question about Dr. kalam or Barak Obama?")

if st.button("Get Answer"):
    if not question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("🤔 Thinking..."):
            #answer = get_best_answer(question, all_text, qa_pipeline)
            answer = smart_answer(question, all_text, qa_pipeline)
        if answer:
            st.success("✅ Answer:")
            st.markdown(f"<div style='background-color:#f0f2f6; padding:12px; border-radius:8px'>{answer}</div>", unsafe_allow_html=True)
        else:
            st.error("No answer found.")
