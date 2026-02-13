"""Shared UI utilities"""
import streamlit as st
import PyPDF2
import io


def parse_pdf_resume(uploaded_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        st.error(f"Error parsing PDF: {str(e)}")
        return ""


def logout():
    """Clear session and rerun"""
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()
