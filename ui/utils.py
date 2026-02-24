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
    """Clear session cookie and session state, then rerun"""
    # Destroy persistent cookie
    session_mgr = st.session_state.get('session_mgr')
    if session_mgr:
        try:
            session_mgr.destroy_session()
        except Exception:
            pass  # cookie may already be gone

    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.show_application_form = False
    st.rerun()
