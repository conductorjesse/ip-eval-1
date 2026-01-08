import streamlit as st

def render_sidebar():
    """
    Renders the sidebar navigation and configuration.
    Returns the selected page.
    """
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to", 
            ["Analysis Setup", "Evaluation Results", "IP Score Matrix", "Tools & Resources"]
        )
        st.divider()
        st.caption("IP Evaluation Tool v1")
        return page

def render_setup_page():
    """
    Renders the Analysis Setup page: User Context & Patent Input.
    """
    st.header("Analysis Setup")
    
    # 1. User Context
    st.subheader("1. User Context & Goals")
    
    with st.expander("Customize your persona", expanded=True):
        col_ctx1, col_ctx2 = st.columns(2)
        with col_ctx1:
            role = st.text_input("Role / Background", value="Scientific Entrepreneur with chemistry expertise")
            goal = st.text_input("Primary Goal", value="Identify low-carbon chemical technologies")
        with col_ctx2:
            criteria = st.text_area("Specific Criteria", value="Looking for modular systems, TRL 4+, avoiding toxic catalysts.", height=100)
            
    # Combine into a single context string for the AI
    user_context = f"""
    **Role:** {role}
    **Goal:** {goal}
    **Specific Criteria:** {criteria}
    """
    st.session_state["user_context"] = user_context
    st.caption("This helps the AI provide more relevant feedback and focus on if the technology matches your specific needs.")

    # 2. Patent Input
    st.divider()
    st.subheader("2. Patent Input")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        main_patent_input = st.text_input(
            "Main Patent (Required)", 
            placeholder="e.g. WO2025235535A2 or URL"
        )
        st.caption("Example: US9138726B2, US10894756B2")
        
        st.write("")
        complementary_input = st.text_area(
            "Complementary Patents (Optional, one per line)",
            placeholder="e.g. US1234567\nUS7654321",
            height=80
        )

    with col2:
        # Align button with input
        st.write("") 
        st.write("")
        analyze_btn = st.button("Evaluate IP", type="primary", use_container_width=True)
        
    return main_patent_input, complementary_input, analyze_btn

import json
from logic import analysis # Correct import path

def render_results_page(evaluation, evaluation_portfolio=None):
    """
    Renders the Analysis Results page with modular sections and chat.
    """
    st.header("Evaluation Results")
    
    if not evaluation:
        st.info("No evaluation available. Please run an analysis in 'Analysis Setup'.")
        return

    # --- Tabs Layout (Reverted Request) ---
    tab_labels = [
        "Technology Overview", 
        "Market & Commercial Analysis", 
        "Further Exploration"
    ]
    
    if evaluation_portfolio:
        tab_labels.append("Portfolio Overview")
        
    tabs = st.tabs(tab_labels)
    
    # Parse Markdown Sections
    eval_data = analysis.parse_evaluation_sections(evaluation)

    # Render Main Analysis Tabs
    # 1. Technology
    with tabs[0]:
        title = "Technology Overview"
        content = eval_data.get(title, "N/A")
        st.markdown(content)
        _render_section_chat(title, content)

    # 2. Market
    with tabs[1]:
        title = "Market & Commercial Analysis"
        content = eval_data.get(title, "N/A")
        st.markdown(content)
        _render_section_chat(title, content)
        
    # 3. Further Exploration
    with tabs[2]:
        title = "Further Exploration"
        content = eval_data.get(title, "N/A")
        st.markdown(content)
        _render_section_chat(title, content)

    # 4. Portfolio (if exists)
    if evaluation_portfolio and len(tabs) > 3:
        with tabs[3]:
            st.markdown(evaluation_portfolio)

def _render_section_chat(title, content):
    """
    Helper to render the specific chat expander for a section.
    """
    history_key = f"chat_history_{title.replace(' ','_')}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
    
    st.divider()
    with st.expander(f"Ask about {title}", expanded=False):
        # Display Local History
        for msg in st.session_state[history_key]:
            st.markdown(f"**{msg['role'].title()}:** {msg['content']}")
        
        # Local Input
        if f"input_{history_key}" not in st.session_state:
             st.session_state[f"input_{history_key}"] = ""
        
        q = st.text_input(f"Question about {title}:", key=f"q_{history_key}")
        
        if st.button("Ask", key=f"btn_{history_key}"):
            if q:
                st.session_state[history_key].append({"role": "user", "content": q})
                
                api_key = st.session_state.get("api_key")
                if api_key:
                    with st.spinner("Thinking..."):
                        section_context = f"Section: {title}\nContent: {content}"
                        ans = analysis.chat_with_patent_context(q, [], section_context, api_key)
                        st.session_state[history_key].append({"role": "assistant", "content": ans})
                        st.rerun()

def render_raw_data_page(patent_data_list):
    """
    Renders the raw scraped patent data.
    Expects a LIST of patent data dicts.
    """
    st.header("Raw Patent Data")
    if not patent_data_list:
        st.info("No patent data available.")
        return
        
    # Ensure it is a list
    if not isinstance(patent_data_list, list):
        patent_data_list = [patent_data_list]

    tabs = st.tabs([p.get('publication_number', f'Patent {i+1}') for i, p in enumerate(patent_data_list)])
    
    for i, tab in enumerate(tabs):
        with tab:
            patent_data = patent_data_list[i]
            st.write(f"**Title:** {patent_data.get('title')}")
            st.write(f"**Publication:** {patent_data.get('publication_number')}")
            st.write(f"**Inventors:** {', '.join(patent_data.get('inventors', []))}")
            
            st.subheader("Abstract")
            st.write(patent_data.get('abstract'))
            
            st.subheader("Claims (Excerpt)")
            claims = patent_data.get('claims', [])
            if claims and isinstance(claims[0], dict):
                st.text("\n".join([f"{c['number']}: {c['text']}" for c in claims[:5]]))
            else:
                st.text("\n".join(claims[:5]))
                
            if patent_data.get('url'):
                st.link_button("View on Google Patents", patent_data['url'])

def render_chat_interface(messages):
    """
    Renders the chat interface. Designed for a narrow column.
    """
    st.subheader("Assistant")
    
    # Display chat messages with a container to allow scrolling if needed (auto-handled)
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
