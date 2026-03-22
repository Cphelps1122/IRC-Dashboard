import streamlit as st
import base64

def render_header():
    # Load the image file
    with open("assets/cgs_logo2.png", "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    # Center it using HTML
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{encoded}" style="max-width: 60%; height: auto;">
        </div>
        """,
        unsafe_allow_html=True
    )
