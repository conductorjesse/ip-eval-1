import os
from dotenv import load_dotenv
from openai import OpenAI
from logic import scraper, analysis

load_dotenv()

def verify():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        return
    
    print(f"API Key found: {api_key[:5]}...")

    # 0. Check connection and models
    print("0. Checking Available Models...")
    try:
        client = OpenAI(api_key=api_key)
        # basic check
        for m in client.models.list():
            if "gpt-5" in m.id:
                print(f" - {m.id}")
                
    except Exception as e:
        print(f"Error listing models: {e}")

    # 1. Scrape
    patent_id = "WO2025235535A2"
    url = f"https://patents.google.com/patent/{patent_id}"
    
    print(f"\n1. Scrape {url}...")
    data = scraper.scrape_patent(url)
    
    # Test PDF Generation
    print("\n1.5 Testing PDF Generation with Unicode...")
    try:
        from logic import report_generator
        test_unicode = "Test Unicode: \u2070 (superscript 0) and “smart quotes”"
        pdf_bytes = report_generator.create_pdf(
            {"title": "Test Patent \u2122", "publication_number": "WO123"},
            test_unicode,
            "User Context"
        )
        if isinstance(pdf_bytes, bytes) and len(pdf_bytes) > 0:
            print(f"PDF Generation Success (bytes generated, size={len(pdf_bytes)}).")
            # Optional: save to check
            with open("test_report.pdf", "wb") as f:
                f.write(pdf_bytes)
                print("Saved test_report.pdf for manual inspection.")
        else:
            print(f"PDF Generation Returned unexpected type/size: {type(pdf_bytes)}")
    except Exception as e:
        print(f"PDF Generation Failed: {e}")

    # 1.6 Verify Markdown Parser (Round 3.3 Update)
    print("\n1.6 Verifying Markdown Parsing Logic...")
    test_md = """
    ### 1. Technology Overview
    Content for tech.
    ### 2. Market & Commercial Analysis
    Content for market.
    ### 3. Further Exploration
    Content for further.
    """
    parsed = analysis.parse_evaluation_sections(test_md)
    print("Parsed Keys:", list(parsed.keys()))
    if "Technology Overview" in parsed and parsed["Technology Overview"] == "Content for tech.":
        print("Parsing Logic Verified.")
    else:
        print("Parsing Logic Failed / Unexpected Output:", parsed)

    # 2. Portfolio Analysis Test (Round 3 Update: List of dicts)
    print("\n2. Testing Portfolio Analysis...")
    try:
        # Round 3 Logic: analysis.analyze_portfolio expects a LIST of patent dicts
        mock_portfolio = [
            {"publication_number": "PAT1", "title": "Invention A", "abstract": "Solves X", "claims": ["Claim 1"]},
            {"publication_number": "PAT2", "title": "Invention B", "abstract": "Solves Y", "claims": ["Claim 1"]}
        ]
        res = analysis.analyze_portfolio(mock_portfolio, "Investor Persona", api_key)
        print(f"Portfolio Analysis Result (snippet): {res[:100]}...")
    except Exception as e:
        print(f"Portfolio Analysis Failed: {e}")

    # 3. Pitch Deck Test - Replaced with Raw Data in UI, but Logic still exists? 
    # Actually User requested to remove Innovator Tools UI, but logic might remain or be removed. 
    # Logic file wasn't changed to remove it, so test can stay or be redundant.
    # Let's keep it to ensure analysis.py didn't break.
    print("\n3. Testing Pitch Deck Generation (Backend)...")
    try:
        res = analysis.generate_pitch_deck({"title": "Test IP", "abstract": "Cool tech"}, "Startup Context", api_key)
        print(f"Pitch Deck Result (snippet): {res[:100]}...")
    except Exception as e:
        print(f"Pitch Deck Gen Failed: {e}")

    # 4. Glossary Test
    print("\n4. Testing Glossary Generation (Backend)...")
    try:
        res = analysis.generate_glossary("The apparatus comprises a plurality of orthogonal axis actuators.", api_key)
        print(f"Glossary Result (snippet): {res[:100]}...")
    except Exception as e:
        print(f"Glossary Gen Failed: {e}")
    
    if not data or not data.get('title'):
        print("Scraping failed.")
        return
    else:
        print(f"Scraping success: {data['title']}")

    # 5. Analyze
    print("\n5. Analyze with Gemini...")
    try:
        context = "Verification Test User"
        evaluation = analysis.analyze_patent(data, context, api_key)
        
        if evaluation and "Technology overview" in evaluation:
            print("Analysis success: Evaluation generated.")
            print("--- EVALUATION START ---")
            print(evaluation[:200] + "...") 
            print("--- EVALUATION END ---")
        else:
            print("Analysis failed or unexpected format.")
            print(f"Output: {evaluation}")
    except Exception as e:
        print(f"Analysis Exception: {e}")

if __name__ == "__main__":
    verify()
