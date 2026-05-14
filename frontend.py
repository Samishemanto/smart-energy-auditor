import streamlit as st
import requests
from streamlit_option_menu import option_menu

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Smart Energy Auditor", page_icon="⚡", layout="wide")

# --- Top Navigation Bar ---
page = option_menu(
    menu_title=None,
    options=["Upload Bill", "Bill History", "About"],
    icons=["cloud-upload", "clock-history", "info-circle"],
    orientation="horizontal",
    default_index=0,
    styles={
        "container": {"padding": "0", "background-color": "#1e1e2e"},
        "icon": {"color": "#f5c518", "font-size": "18px"},
        "nav-link": {"font-size": "16px", "color": "white", "--hover-color": "#333355"},
        "nav-link-selected": {"background-color": "#f5c518", "color": "black"},
    },
)

st.markdown("---")

# ── Upload Bill ──────────────────────────────────────────────────────────────
if page == "Upload Bill":
    st.header("Upload a Bill")
    st.markdown("Upload a PNG or JPG image of your energy bill to extract details automatically.")

    uploaded_file = st.file_uploader("Choose an image of your bill", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            st.image(uploaded_file, caption="Uploaded Bill", use_container_width=True)

        with col2:
            if st.button("Process Bill", type="primary"):
                with st.spinner("Running OCR and parsing bill..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/upload-bill",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success("Bill processed successfully!")
                            st.subheader("Extracted Details")
                            st.metric("Provider", data.get("provider", "Unknown"))
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Amount Due", f"£{data.get('amount_due', 'N/A')}")
                                st.metric("Bill Date", data.get("bill_date") or "Not found")
                            with col_b:
                                st.metric("Usage (kWh)", data.get("usage_kwh") or "Not found")
                                st.metric("Due Date", data.get("due_date") or "Not found")
                            if data.get("account_number"):
                                st.info(f"Account Number: {data['account_number']}")
                            with st.expander("Raw OCR Text Preview"):
                                st.text(data.get("raw_text_preview") or data.get("extracted_text", ""))
                        else:
                            st.error(f"Error {response.status_code}: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to the backend. Make sure the server is running on port 8000.")

# ── Bill History ─────────────────────────────────────────────────────────────
elif page == "Bill History":
    st.header("Bill History")

    col_title, col_btn = st.columns([6, 1])
    with col_btn:
        if st.button("Refresh"):
            st.rerun()

    try:
        response = requests.get(f"{API_URL}/bills", timeout=3)
        if response.status_code == 200:
            bills = response.json()
            if bills:
                for bill in bills:
                    with st.expander(f"#{bill['id']} — {bill['filename']} ({bill['provider']})"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Amount Due", f"£{bill.get('amount_due', 'N/A')}")
                        c2.metric("Usage (kWh)", bill.get("usage_kwh") or "N/A")
                        c3.metric("Bill Date", bill.get("bill_date") or "N/A")
                        if bill.get("account_number"):
                            st.caption(f"Account: {bill['account_number']}")
            else:
                st.info("No bills uploaded yet.")
        else:
            st.warning("Could not load bill history.")
    except requests.exceptions.ConnectionError:
        st.warning("Backend not reachable. Start the server first.")

# ── About ────────────────────────────────────────────────────────────────────
elif page == "About":
    st.header("About Smart Energy Auditor")
    st.markdown("""
**Smart Energy Auditor** helps you digitise and track your energy bills automatically.

**How it works:**
1. Upload a photo (PNG/JPG) of your electricity or gas bill
2. OCR extracts the text from the image
3. The parser detects your provider and pulls out key fields
4. Results are saved to a local database for history tracking

**Supported providers:**
- Scottish Power
- British Gas
- Octopus Energy
- Generic fallback for other providers

**Tech stack:**
- Backend: FastAPI + SQLite
- OCR: Tesseract via pytesseract
- Frontend: Streamlit
    """)
