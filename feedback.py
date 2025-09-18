import streamlit as st
import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/…/your/unique/webhook"

st.title("My App")

# Feedback dialog
@st.dialog("💬 Feedback")
def feedback_dialog():
    feedback = st.text_area("Enter your feedback")
    if st.button("Submit Feedback"):
        if feedback.strip():
            webhook_url = st.secrets["SLACK_WEBHOOK_URL"]
            payload = {"text": f"📩 Feedback:\n{feedback}"}
            response = requests.post(webhook_url, json=payload)

            if response.status_code == 200:
                st.success("✅ Feedback sent to Slack!")
            else:
                st.error("❌ Failed to send feedback.")
        else:
            st.warning("⚠️ Please enter feedback before submitting.")

# Button to open feedback dialog
if st.button("Give Feedback"):
    feedback_dialog()
