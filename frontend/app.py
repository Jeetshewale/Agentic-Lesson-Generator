import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Agentic Lesson Generator", page_icon="🤖", layout="wide")

N8N_WEBHOOK = "http://localhost:5678/webhook/generate-lesson"
BACKEND_URL = "http://localhost:8000"

st.title("🤖 Agentic Lesson Content Generator")
st.markdown("Generates, evaluates, and autonomously regenerates content until it clears a strict rubric.")

topic = st.text_input("Enter a lesson topic:", "Introduction to Retrieval-Augmented Generation (RAG)")
force_error = st.toggle("Inject Deliberate Error (For Demo Purposes)", value=False)

if st.button("Generate Lesson", type="primary"):
    with st.status("Starting Agentic Loop...", expanded=True) as status:
        st.write("🚀 Requesting optimal prompt via RL Bandit...")
        
        # Call n8n Webhook
        try:
            st.write("⚙️ Generator and Evaluator working in n8n...")
            response = requests.post(N8N_WEBHOOK, json={
                "topic": topic,
                "force_error": force_error
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's the final output
                status.update(label="Process Complete!", state="complete", expanded=False)
                
                st.success("Lesson generated and passed evaluation!")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📚 Final Lesson")
                    # Safely handle the response structure from n8n
                    if isinstance(data, list) and len(data) > 0:
                        lesson_text = data[0].get("original_lesson", "Could not parse lesson text.")
                    elif isinstance(data, dict):
                        lesson_text = data.get("original_lesson", "Could not parse lesson text.")
                    else:
                        lesson_text = str(data)
                    
                    st.markdown(lesson_text)
                    
                with col2:
                    st.subheader("📊 RL Bandit Stats")
                    try:
                        stats_res = requests.get(f"{BACKEND_URL}/stats")
                        if stats_res.status_code == 200:
                            stats = stats_res.json()
                            for variant, win_rate in stats.items():
                                st.progress(win_rate, text=f"{variant}: {win_rate:.1%} success rate")
                    except Exception as e:
                        st.warning("Could not fetch RL stats. Is backend running?")
                        
            else:
                status.update(label="Error in Workflow", state="error")
                st.error(f"n8n Webhook returned status {response.status_code}")
                
        except Exception as e:
            status.update(label="Connection Error", state="error")
            st.error(f"Failed to connect to n8n webhook: {str(e)}")
