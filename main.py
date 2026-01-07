import streamlit as st
import os
from dotenv import load_dotenv

# Import logic modules
from logic import scraper
from logic import analysis
from ui import layout

# Load environment variables (optional for local dev if not using secrets, but we use secrets now)
# load_dotenv()

# Page Config
st.set_page_config(page_title="IP Evaluation Tool", layout="wide", initial_sidebar_state="expanded")

# --- Session State Initialization ---
if "patent_data" not in st.session_state:
    st.session_state["patent_data"] = None
if "evaluation" not in st.session_state:
    st.session_state["evaluation"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "api_key" not in st.session_state:
    # Try to get from secrets
    try:
        st.session_state["api_key"] = st.secrets["GEMINI_API_KEY"]
    except FileNotFoundError:
        st.session_state["api_key"] = None
    except KeyError:
        st.session_state["api_key"] = None

# --- UI Rendering ---

# Sidebar Navigation
selected_page = layout.render_sidebar()

st.title("IP Evaluation Tool")

# Main Layout: Content (Left) vs Chat (Right)
col_content, col_chat = st.columns([7, 3])

# --- LEFT COLUMN: Main Workflow ---
with col_content:
    if selected_page == "Analysis Setup":
        patent_input, analyze_btn = layout.render_setup_page()
        
        if analyze_btn:
            api_key = st.session_state.get("api_key")
            if not api_key:
                st.error("Please provide a Gemini API Key in `.streamlit/secrets.toml`.")
            elif not patent_input:
                st.warning("Please enter a patent number or URL.")
            else:
                # 1. Normalize URL
                if "google.com/patent" not in patent_input:
                     patent_url = f"https://patents.google.com/patent/{patent_input.strip()}"
                else:
                    patent_url = patent_input.strip()

                with st.spinner(f"Scraping patent from {patent_url}..."):
                    data = scraper.scrape_patent(patent_url)
                
                if data:
                    st.session_state["patent_data"] = data
                    st.success("Patent data retrieved!")
                    
                    # 2. Analyze with Gemini
                    with st.spinner("Analyzing with Gemini..."):
                        user_context = st.session_state.get("user_context", "")
                        evaluation = analysis.analyze_patent(data, user_context, api_key)
                        st.session_state["evaluation"] = evaluation
                        st.session_state["chat_history"] = [] # Reset chat
                        
                        st.info("Analysis Complete. Go to 'Evaluation Results' or 'Raw Data' tabs to view.")
                else:
                    st.error("Failed to scrape patent. Please check the ID/URL and try again.")
    
    elif selected_page == "Evaluation Results":
        layout.render_results_page(st.session_state["evaluation"])
        
    elif selected_page == "Raw Data":
        layout.render_raw_data_page(st.session_state["patent_data"])

# --- RIGHT COLUMN: Persistent Chat ---
with col_chat:
    layout.render_chat_interface(st.session_state["chat_history"])
    
    # Check if we have context to chat about
    if st.session_state["evaluation"] or st.session_state["patent_data"]:
        if prompt := st.chat_input("Ask a question about this patent..."):
            # Append user message
            st.session_state["chat_history"].append({"role": "user", "content": prompt})
            st.rerun()

# Handle Chat Generation (if last message is user)
if st.session_state["chat_history"] and st.session_state["chat_history"][-1]["role"] == "user":
    with col_chat:
        with st.chat_message("model"):
            with st.spinner("Thinking..."):
                api_key = st.session_state.get("api_key")
                
                # History excluding current prompt
                previous_history = st.session_state["chat_history"][:-1]
                gemini_hist = analysis.format_chat_history(previous_history)
                
                # Patent Context
                p_data = st.session_state["patent_data"]
                patent_context_str = ""
                if p_data:
                    patent_context_str = (
                        f"Title: {p_data.get('title')}\n"
                        f"Abstract: {p_data.get('abstract')}\n"
                        f"Claims (excerpt): {str(p_data.get('claims'))[:20000]}\n"
                        f"Description (excerpt): {str(p_data.get('description'))[:20000]}"
                    )
                
                response_text = analysis.chat_with_patent_context(
                    st.session_state["chat_history"][-1]["content"], 
                    gemini_hist, 
                    patent_context_str, 
                    api_key
                )
                
                if response_text:
                     # This might print twice if we aren't careful, but st.chat_message("model") here is correct.
                     st.markdown(response_text)
                     st.session_state["chat_history"].append({"role": "model", "content": response_text})
                     st.rerun() 
