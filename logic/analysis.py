from openai import OpenAI
import os

def get_client(api_key):
    """
    Configures and returns the OpenAI Client.
    """
    if not api_key:
        raise ValueError("API Key is required")
    
    return OpenAI(api_key=api_key)

def analyze_patent(patent_data, user_context, api_key):
    """
    Analyzes the patent data against the evaluation framework using OpenAI GPT-5 mini.
    """
    try:
        client = get_client(api_key)
        
        # Prepare data strings
        claims_text = ""
        if patent_data.get('claims'):
            if isinstance(patent_data['claims'][0], dict):
                claims_text = "\n".join([f"{c['number']}: {c['text']}" for c in patent_data['claims']])
            else:
                claims_text = "\n".join(patent_data['claims'])
        
        description_text = "\n".join(patent_data.get('description', []))
        
        system_prompt = "Act as an expert IP analyst, Tech Transfer Officer, and commercialization specialist."
        
        user_prompt = f"""
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
        
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing patent: {str(e)}"

def format_chat_history(streamlit_messages):
    """
    Converts Streamlit chat history [{'role': 'user', 'content': '...'}, ...]
    to OpenAI history format.
    Essentially a pass-through but ensures keys are correct.
    """
    openai_history = []
    for msg in streamlit_messages:
        role = "user" if msg["role"] == "user" else "assistant"
        openai_history.append({"role": role, "content": msg["content"]})
    return openai_history

def chat_with_patent_context(user_message, history, patent_context_str, api_key):
    """
    Sends a message to OpenAI with the patent context (if first message) and history.
    """
    try:
        client = get_client(api_key)
        
        messages = []
        
        # System context
        system_instruction = f"""
        You are an assistant helping a user understand a patent.
        Here is the Patent Context:
        {patent_context_str}
        
        Answer the user's questions based on this context. Keep answers concise.
        """
        messages.append({"role": "system", "content": system_instruction})
        
        # Append history (which should already be in OpenAI format via format_chat_history)
        if history:
            messages.extend(history)
            
        # Append current user message
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error in chat: {str(e)}"
