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
    
    if not data or not data.get('title'):
        print("Scraping failed.")
        return
    else:
        print(f"Scraping success: {data['title']}")

    # 2. Analyze
    print("\n2. Analyze with Gemini...")
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
