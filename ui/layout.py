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

def render_results_page(main_eval, portfolio_eval=None):
    """
    Renders the evaluation results.
    """
    st.header("Evaluation Results")
    if not main_eval:
        st.info("No evaluation generated yet. Please go to 'Analysis Setup' to start.")
        return

    # Tabs: Tech, Market, Next Steps are for MAIN patent.
    # Portfolio Overview is for PORTFOLIO (if exists).
    
    tabs_list = ["Technology", "Market & Commercial", "Next Steps"]
    if portfolio_eval:
        tabs_list.append("Portfolio Overview")
    
    tabs = st.tabs(tabs_list)
    
    # Parse Main Eval
    try:
        parts = main_eval.split("### ")
        tech_content = "### " + parts[1] if len(parts) > 1 else main_eval
        market_content = "### " + parts[2] if len(parts) > 2 else ""
        next_steps_content = "### " + parts[3] if len(parts) > 3 else ""
    except:
        tech_content = main_eval
        market_content = "Error parsing response structure."
        next_steps_content = ""

    with tabs[0]:
        st.markdown(tech_content)
    with tabs[1]:
        if market_content:
            st.markdown(market_content)
        else:
            st.info("Market analysis not found.")
    with tabs[2]:
        if next_steps_content:
            st.markdown(next_steps_content)
        else:
            st.info("Next steps not found.")
            
    if portfolio_eval and len(tabs) > 3:
        with tabs[3]:
            st.markdown(portfolio_eval)

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
