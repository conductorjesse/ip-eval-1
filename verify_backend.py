import os
from dotenv import load_dotenv
import google.generativeai as genai
from logic import scraper, analysis

load_dotenv()

def verify():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return
    
    print(f"API Key found: {api_key[:5]}...")

    # 0. Check connection and models
    print("0. Checking Available Models...")
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

    # 1. Scrape
    patent_id = "WO2025235535A2"
    url = f"https://patents.google.com/patent/{patent_id}"
    
    print(f"\n1. Scrape {url}...")
    data = scraper.scrape_patent(url)
    
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
