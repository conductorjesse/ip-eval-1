import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

def load_questions(csv_path):
    """Loads questions from the CSV file."""
    try:
        df = pd.read_csv(csv_path)
        # Structure: Factor, Question, Option 1...5
        # Parse into a structured dict
        categories = {
            'A': 'Legal Status',
            'B': 'Technology',
            'C': 'Market Conditions',
            'D': 'Finance',
            'E': 'Strategy'
        }
        
        questions = []
        for _, row in df.iterrows():
            if pd.isna(row['Factor']) or not row['Factor'].strip():
                continue
            
            factor_code = str(row['Factor']).strip()
            cat_code = factor_code[0]
            
            # Simple parsing options
            options = []
            for i in range(1, 6):
                opt_text = row.get(f'Option {i}')
                if pd.notna(opt_text):
                    options.append(str(opt_text))
            
            questions.append({
                "code": factor_code,
                "category_code": cat_code,
                "category": categories.get(cat_code, "Other"),
                "question": row['Question'],
                "options": options
            })
        return questions
    except Exception as e:
        st.error(f"Error loading IP Score CSV: {e}")
        return []

def render_score_page():
    st.header("IP Score Matrix")
    st.markdown("Evaluate your IP based on the 5-point assessment matrix.")
    st.caption("Based on the [EPO IPScore methodology](https://www.epo.org/en/searching-for-patents/business/ipscore).")

    # Path to CSV - assuming it is in planning folder or moved to logic
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "planning", "IPscore-full-table.csv")
    
    questions = load_questions(csv_path)
    
    if "ip_scores" not in st.session_state:
        st.session_state["ip_scores"] = {}

    # Group by category
    categories = sorted(list(set(q['category'] for q in questions)))
    
    # --- 1. Results Visualization (Top) ---
    if questions:
        # Calculate category averages
        cat_scores = {}
        for cat in categories:
            cat_qs = [q for q in questions if q['category'] == cat]
            total = 0
            count = 0
            for q in cat_qs:
                val = st.session_state["ip_scores"].get(q['code'], 1) # default 1 min
                total += val
                count += 1
            cat_scores[cat] = total / count if count else 0
        
        # Spider Chart
        data_vals = [cat_scores[cat] for cat in categories]
        data_cats = categories
        
        # Close the loop
        data_vals.append(data_vals[0])
        data_cats.append(data_cats[0])
        
        fig = go.Figure(data=go.Scatterpolar(
            r=data_vals,
            theta=data_cats,
            fill='toself',
            name='IP Score'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            showlegend=False,
            margin=dict(t=20, b=20, l=40, r=40),
            height=400
        )
        
        st.plotly_chart(fig)
        
        # Summary Text
        score_avg = sum(data_vals[:-1]) / len(categories)
        st.metric("Overall IP Score", f"{score_avg:.1f} / 5.0")
        
        st.divider()

    # --- 2. Input Form (Bottom, Collapsible) ---
    st.subheader("Assessment Questions")
    with st.form("ip_score_form"):
        # Use a simple flat counter to ensure absolute key uniqueness
        # This avoids any issues with duplicate codes, categories, or loop indices
        radio_counter = 0
        
        for cat in categories:
            with st.expander(f"{cat} Factors", expanded=False):
                cat_qs = [q for q in questions if q['category'] == cat]
                
                for q in cat_qs:
                    current_val = st.session_state["ip_scores"].get(q['code'], 0) # default 0
                    
                    # Initialize index
                    idx = 0
                    if current_val > 0:
                        idx = current_val - 1
                    
                    # Safe key using flat counter
                    unique_key = f"radio_{q['code']}_{radio_counter}"
                    radio_counter += 1
                    
                    selected = st.radio(
                        f"{q['code']}: {q['question']}",
                        options=q['options'],
                        index=idx if idx < len(q['options']) else 0,
                        key=unique_key
                    )
                    
                    # Extract score
                    try:
                        score = int(selected.split(':')[0])
                    except:
                        score = 1
                    
                    st.session_state["ip_scores"][q['code']] = score
                    st.write("") # Spacer
        
        submitted = st.form_submit_button("Update Score Analysis")
