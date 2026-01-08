import streamlit as st
from logic import analysis

def render_tools_page():
    st.header("Tools & Resources")
    
    # Check if we have patent data
    patent_data = st.session_state.get("patent_data")
    if not patent_data:
        st.warning("Please first search/scrape a patent in 'Analysis Setup' to use these tools effectively.")
    
    tab_lookup, tab_raw = st.tabs(["Web Lookups", "Raw Patent Data"])
    
    with tab_lookup:
        st.subheader("Targeted Web Lookups")
        st.markdown("Quickly find relevant external information.")
        
        # Determine query base
        query_base = ""
        if patent_data:
            if isinstance(patent_data, list):
                query_base = " ".join([p.get('title', '') for p in patent_data[:2]])
            else:
                query_base = patent_data.get('title', '')
        
        col_search, col_links = st.columns([2, 1])
        
        with col_search:
            search_topic = st.text_input("Refine Search Topic", value=query_base, placeholder="Enter keywords...")
        
        with col_links:
            st.markdown("#### quick Links")
            if search_topic:
                q = search_topic.replace(' ', '+')
                st.markdown(f"- [Google Patents: Prior Art](https://patents.google.com/?q={q}&top_terms=prior+art)")
                st.markdown(f"- [Google Search: Competitors](https://www.google.com/search?q={q}+competitors+market)")
                st.markdown(f"- [Google Search: Market Size](https://www.google.com/search?q={q}+market+size+TAM)")
                st.markdown(f"- [Google Search: News](https://www.google.com/search?q={q}&tbm=nws)")
            else:
                st.caption("Enter a topic to generate links.")

    with tab_raw:
        st.subheader("Raw Patent Data")
        
        # Determine what to show
        # If portfolio exists, it acts as the master list
        data_to_show = st.session_state.get("portfolio_data")
        if not data_to_show:
             # Fallback to single patent data
             single = st.session_state.get("patent_data")
             if single:
                 data_to_show = [single]
        
        if not data_to_show:
            st.info("No patent data available.")
        else:
            tabs = st.tabs([p.get('publication_number', f'Patent {i+1}') for i, p in enumerate(data_to_show)])
    
            for i, tab in enumerate(tabs):
                with tab:
                    patent_data = data_to_show[i]
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
