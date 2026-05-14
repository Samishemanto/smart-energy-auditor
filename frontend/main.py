import streamlit as st
import requests

st.title("🔌 Smart Energy Auditor")

if st.button("Check Backend Status"):
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            data = response.json()
            st.success(f"Backend Status: {data['status']} 🟢")
        else:
            st.error("Backend returned an error ❌")
    except Exception as e:
        st.error(f"Error: {e}")
