import google.generativeai as genai
import os

def get_model(api_key):
    """
    Configures and returns the Gemini GenerativeModel.
    """
    if not api_key:
        raise ValueError("API Key is required")
    
    genai.configure(api_key=api_key)
    # Using 3 Flash Preview as requested
    return genai.GenerativeModel('gemini-3-flash-preview')

def analyze_patent(patent_data, user_context, api_key):
    """
    Analyzes the patent data against the evaluation framework using Gemini.
    """
    try:
        model = get_model(api_key)
        
        # Prepare data strings
        claims_text = ""
        if patent_data.get('claims'):
            # Convert list of dicts or strings to text
            if isinstance(patent_data['claims'][0], dict):
                claims_text = "\n".join([f"{c['number']}: {c['text']}" for c in patent_data['claims']])
            else:
                claims_text = "\n".join(patent_data['claims'])
        
        description_text = "\n".join(patent_data.get('description', []))
        
        # Truncate if extremely large, though 1.5 Flash has 1M context.
        # Let's include everything we can.
        
        prompt = f"""
        Act as an expert IP analyst, Tech Transfer Officer, and commercialization specialist.
        Evaluate the following patent based on the provided user context.
        
        **User Context:**
        {user_context}
        
        **Patent Data:**
        Title: {patent_data.get('title')}
        Publication Number: {patent_data.get('publication_number')}
        Inventors: {', '.join(patent_data.get('inventors', []))}
        Assignee: {', '.join(patent_data.get('assignees', {}).get('current', []))}
        
        Abstract:
        {patent_data.get('abstract')}
        
        Claims (excerpt):
        {claims_text[:50000]} 
        
        Description (excerpt):
        {description_text[:100000]}
        
        **Instruction:**
        Provide a detailed evaluation based on the following framework.
        Provide concise but insightful responses for each sub-bullet.
        
        IMPORTANT: Format the output using the exact Markdown headers below. Do not deviate from this structure.
        
        ### 1. Technology Overview
        * **Background & Context:** [Response]
        * **Problem Solved (Value Proposition):** [Response]
        * **Solution Description (Technical Approach):** [Response]
        * **Technology Readiness Level (TRL) Assessment (1-9 scale):** [Estimate TRL and explain why]
        * **Unique Technical Advantages:** [Response]
        * **Technical Deficiencies & Risks:** [Response]
        * **R&D Milestones to Commercialization:** [Response]

        ### 2. Market & Commercial Analysis
        * **Target Market(s) & Segmentation:** [Response]
        * **Commercial Readiness Level (CRL) Assessment (1-9 scale):** [Estimate CRL and explain why]
        * **Market Size, Growth, Trends:** [Response]
        * **Freedom to Operate (FTO) / Competitive Landscape Snapshot:** [Identify potential incumbents or crowding based on context]
        * **Value Chain Positioning:** [Response]
        * **Barriers to Entry:** [Response]
        * **Regulatory, Compliance, & Policy:** [Response]

        ### 3. Further Exploration
        * **Questions for Tech Transfer Office:** [Response]
        * **Questions for Inventors:** [Response]
        * **Key Outstanding Questions:** [Response]
        * **Potential Follow-on Markets:** [Response]
        
        Note: For 'External internet searches' (e.g. other patents), rely on your internal knowledge or the 'Similar Documents' identified in the patent text if available.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error analyzing patent: {str(e)}"

def format_chat_history(streamlit_messages):
    """
    Converts Streamlit chat history [{'role': 'user', 'content': '...'}, ...]
    to Gemini history format.
    """
    gemini_history = []
    for msg in streamlit_messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    return gemini_history

def chat_with_patent_context(user_message, history, patent_context_str, api_key):
    """
    Sends a message to Gemini with the patent context (if first message) and history.
    """
    try:
        model = get_model(api_key)
        
        # If history is empty, prepend the system context
        if not history:
            system_instruction = f"""
            You are an assistant helping a user understand a patent.
            Here is the Patent Context:
            {patent_context_str}
            
            Answer the user's questions based on this context. Keep answers concise.
            """
            # We can't easily use system_instruction in standard generate_content without context caching or just prepending.
            # We'll just prepend it to the first message or history.
            history = [{"role": "user", "parts": [system_instruction]}] # Seed context
            # Acknowledge logic? 
            # Or better: use system_instruction argument if supported, or just put it in the list.
            # Since we are using chat, we can start the chat with this history.
        
        chat = model.start_chat(history=history)
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"Error in chat: {str(e)}"
