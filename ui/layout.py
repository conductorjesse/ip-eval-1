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
    st.subheader("1. User Context")
    default_context = "I am a startup founder focused on critical minerals exploration. I am looking for technologies that improve the efficiency of mineral recovery from unconventional sources (e.g., brines, mine tailings) or reduce the environmental impact of extraction."
    user_context = st.text_area(
        "Describe your background and goals:",
        value=st.session_state.get("user_context", default_context),
        height=150
    )
    st.session_state["user_context"] = user_context
    st.info("The more specific your context, the better the evaluation.")

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
