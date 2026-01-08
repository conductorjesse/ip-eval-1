import streamlit as st

def render_sidebar():
    """
    Renders the sidebar navigation and configuration.
    Returns the selected page.
    """
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Analysis Setup", "Evaluation Results", "Raw Data"])
        
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
    st.caption("This context helps the AI verify if the technology matches your specific needs.")

    # 2. Patent Input
    st.divider()
    st.subheader("2. Target Patent")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        patent_input = st.text_input(
            "Enter Patent URL or Number (Google Patents)", 
            placeholder="e.g. WO2025235535A2 or https://patents.google.com/patent/WO2025235535A2"
        )
    with col2:
        # Align button with input
        st.write("") 
        st.write("")
        analyze_btn = st.button("Evaluate IP", type="primary", use_container_width=True)
        
    return patent_input, analyze_btn

def render_results_page(evaluation_text):
    """
    Renders the Gemini evaluation results.
    """
    st.header("Evaluation Results")
    if not evaluation_text:
        st.info("No evaluation generated yet. Please go to 'Analysis Setup' to start.")
        return

    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["Technology", "Market & Commercial", "Next Steps"])
    
    # We need to parse the markdown to split it into tabs, or just render sections.
    # Since the AI output is structured, we can try to split by headers. 
    # But for robustness, if parsing fails, we fallback to showing full text.
    
    try:
        parts = evaluation_text.split("### ")
        # parts[0] might be intro text
        # parts[1] is Tech Overview
        # parts[2] is Market
        # parts[3] is Further Exploration
        
        tech_content = "### " + parts[1] if len(parts) > 1 else evaluation_text
        market_content = "### " + parts[2] if len(parts) > 2 else ""
        next_steps_content = "### " + parts[3] if len(parts) > 3 else ""
        
        with tab1:
            st.markdown(tech_content)
        with tab2:
            if market_content:
                st.markdown(market_content)
            else:
                st.info("Market analysis not found in response.")
        with tab3:
            if next_steps_content:
                st.markdown(next_steps_content)
            else:
                st.info("Next steps not found in response.")
            
    except Exception:
        # Fallback
        st.markdown(evaluation_text)

def render_raw_data_page(patent_data):
    """
    Renders the raw scraped patent data.
    """
    st.header("Raw Patent Data")
    if not patent_data:
        st.info("No patent data available. Please go to 'Analysis Setup' to start.")
        return

    st.write(f"**Title:** {patent_data.get('title')}")
    st.write(f"**Publication Number:** {patent_data.get('publication_number')}")
    st.write(f"**Inventor(s):** {', '.join(patent_data.get('inventors', []))}")
    st.write(f"**Assignee(s):** {', '.join(patent_data.get('assignees', {}).get('current', []))}")
    
    st.subheader("Abstract")
    st.write(patent_data.get('abstract'))
    
    st.subheader("Claims")
    claims = patent_data.get('claims', [])
    if claims and isinstance(claims[0], dict):
        for c in claims:
            st.text(f"{c['number']}: {c['text']}")
    else:
        st.text("\n".join(claims))
        
    st.subheader("Description")
    st.caption("Excerpt")
    desc = patent_data.get('description', [])
    st.text("\n".join(desc)[:5000] + "...")

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
