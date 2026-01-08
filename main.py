import streamlit as st
import os
from dotenv import load_dotenv

# Import logic modules
from logic import scraper
from logic import analysis
from ui import layout

# Load environment variables
load_dotenv()

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
    # 1. Try secrets
    try:
        st.session_state["api_key"] = st.secrets["OPENAI_API_KEY"]
    except (FileNotFoundError, KeyError):
        # 2. Try env
        st.session_state["api_key"] = os.getenv("OPENAI_API_KEY")

# --- UI Rendering ---

# Sidebar Navigation
selected_page = layout.render_sidebar()

st.title("IP Evaluation Tool")

# Main Layout: Content (Left) vs Chat (Right)
col_content, col_chat = st.columns([7, 3])

# --- LEFT COLUMN: Main Workflow ---
with col_content:
    if selected_page == "Analysis Setup":
        main_input, comp_input, analyze_btn = layout.render_setup_page()
        
        if analyze_btn:
            api_key = st.session_state.get("api_key")
            if not api_key:
                st.error("Please provide an OpenAI API Key in `.streamlit/secrets.toml` or `.env`.")
            elif not main_input:
                st.warning("Please enter a Main Patent.")
            else:
                # 1. Scrape Main Patent
                if "google.com/patent" not in main_input:
                     main_url = f"https://patents.google.com/patent/{main_input.strip()}"
                else:
                    main_url = main_input.strip()

                st.session_state["patent_data"] = None # Clear old
                st.session_state["portfolio_data"] = None
                
                with st.spinner(f"Scraping Main Patent..."):
                    main_data = scraper.scrape_patent(main_url)
                
                if main_data:
                    st.session_state["patent_data"] = main_data # Main is single dict
                    
                    # 2. Scrape Complementary
                    comp_patents_data = []
                    if comp_input:
                        comp_lines = [l.strip() for l in comp_input.split('\n') if l.strip()]
                        progress_bar = st.progress(0)
                        for i, c_in in enumerate(comp_lines):
                            if "google.com/patent" not in c_in:
                                c_url = f"https://patents.google.com/patent/{c_in}"
                            else:
                                c_url = c_in
                            with st.spinner(f"Scraping Complementary {c_in}..."):
                                c_data = scraper.scrape_patent(c_url)
                                if c_data:
                                    comp_patents_data.append(c_data)
                            progress_bar.progress((i+1)/len(comp_lines))
                    
                    st.session_state["portfolio_data"] = [main_data] + comp_patents_data if comp_patents_data else None

                    st.success("Patent data retrieved!")
                    
                    # 3. Analyze Main Patent
                    user_context = st.session_state.get("user_context", "")
                    st.session_state["chat_history"] = [] 
                    
                    with st.spinner("Analyzing Main Patent..."):
                         evaluation_main = analysis.analyze_patent(main_data, user_context, api_key)
                         st.session_state["evaluation"] = evaluation_main
                    
                    # 4. Analyze Portfolio (if exists)
                    if st.session_state["portfolio_data"]:
                        with st.spinner("Analyzing Portfolio..."):
                             # We can pass the whole list (Main + Complements)
                             evaluation_portfolio = analysis.analyze_portfolio(st.session_state["portfolio_data"], user_context, api_key)
                             st.session_state["evaluation_portfolio"] = evaluation_portfolio
                    else:
                        st.session_state["evaluation_portfolio"] = None

                    st.info("Analysis Complete. Go to 'Evaluation Results'.")
                else:
                    st.error("Failed to scrape Main Patent.")
    
    elif selected_page == "Evaluation Results":
        # Render Results
        layout.render_results_page(
            st.session_state.get("evaluation"), 
            st.session_state.get("evaluation_portfolio")
        )
        
        # Download PDF Section (Simple support for now, maybe just first one or raw text)
        if st.session_state["evaluation"] and st.session_state["patent_data"]:
            st.divider()
            
            # For V1 portfolio PDF, we might need updates, but let's just dump the text if multiple
            # Or if single, use the existing logic.
            # report_generator expects single dict.
            
            p_data_for_pdf = {}
            if isinstance(st.session_state["patent_data"], list):
                if len(st.session_state["patent_data"]) == 1:
                    p_data_for_pdf = st.session_state["patent_data"][0]
                else:
                    p_data_for_pdf = {"title": "Portfolio Analysis", "publication_number": "Multiple"}
            else:
                 p_data_for_pdf = st.session_state["patent_data"]
            
            col_dl1, col_dl2 = st.columns([3, 1])
            with col_dl2:
                from logic import report_generator
                
                pdf_bytes = report_generator.create_pdf(
                    p_data_for_pdf,
                    st.session_state["evaluation"],
                    st.session_state.get("user_context", "No context provided.")
                )
                
                st.download_button(
                    label="Download Report as PDF",
                    data=pdf_bytes,
                    file_name=f"IP_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
    elif selected_page == "Raw Data":
        # Hidden / Moved to Tools
        pass

    elif selected_page == "IP Score Matrix":
        from ui import ip_score
        ip_score.render_score_page()
    
    elif selected_page == "Tools & Resources":
        from ui import tools
        tools.render_tools_page()

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
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                api_key = st.session_state.get("api_key")
                
                # History excluding current prompt
                previous_history = st.session_state["chat_history"][:-1]
                openai_hist = analysis.format_chat_history(previous_history)
                
                # Patent Context
                # Handle list
                p_data_obj = st.session_state["patent_data"]
                patent_context_str = ""
                
                if isinstance(p_data_obj, list):
                    for p in p_data_obj:
                         patent_context_str += (
                            f"\n--- {p.get('publication_number')} ---\n"
                            f"Title: {p.get('title')}\n"
                            f"Abstract: {p.get('abstract')}\n"
                            f"Claims (excerpt): {str(p.get('claims'))[:5000]}\n"
                        )
                elif p_data_obj:
                     patent_context_str = (
                        f"Title: {p_data_obj.get('title')}\n"
                        f"Abstract: {p_data_obj.get('abstract')}\n"
                        f"Claims (excerpt): {str(p_data_obj.get('claims'))[:20000]}\n"
                        f"Description (excerpt): {str(p_data_obj.get('description'))[:20000]}"
                    )
                
                response_text = analysis.chat_with_patent_context(
                    st.session_state["chat_history"][-1]["content"], 
                    openai_hist, 
                    patent_context_str, 
                    api_key
                )
                
                if response_text:
                     # This might print twice if we aren't careful, but st.chat_message("assistant") here is correct.
                     st.markdown(response_text)
                     st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
                     st.rerun() 
