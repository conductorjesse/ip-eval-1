import requests
from bs4 import BeautifulSoup
import json
import re
import argparse
import sys

def clean_text(tag):
    """
    Extracts text from a BeautifulSoup tag, converting <sub> and <sup> 
    tags to their Unicode equivalents.
    """
    if not tag:
        return None
    
    # We work on a copy to avoid destroying the original tree if it's needed later (though here we process linearly)
    # However, simple copy or in-place modification is fine.
    # To be safe and simple, we'll just modify the tag found.
    # But if we modify 'tag', and 'tag' is a child of something we iterate later, it might be an issue?
    # Actually, we extract strings. modifying the tag *in place* before get_text is the best way.
    
    # Maps for unicode conversion
    SUB_MAP = str.maketrans("0123456789+-=()aehijklmnoprstuvx", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ")
    SUP_MAP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
    
    # Find all sub/sup recursively
    # We need to list them first because modification might affect iterator? 
    # find_all returns a list, so it's safe.
    
    for sub in tag.find_all('sub'):
        if sub.string:
            new_text = sub.string.translate(SUB_MAP)
            sub.string.replace_with(new_text)
        sub.unwrap()
        
    for sup in tag.find_all('sup'):
        if sup.string:
            new_text = sup.string.translate(SUP_MAP)
            sup.string.replace_with(new_text)
        sup.unwrap()
        
    return tag.get_text(strip=True)

def scrape_patent(url):
    """
    Scrapes a Google Patent page and returns a dictionary of the organized data.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {
        'url': url,
        'title': None,
        'abstract': None,
        'classifications': [],
        'publication_number': None,
        'country': None,
        'inventors': [],
        'assignees': {
            'current': [],
            'original': []
        },
        'events': [],
        'status': None,
        'claims': [],
        'description': [],
        'similar_documents': []
    }

    try:
        # 1. Title
        title_tag = soup.find('h1', itemprop='pageTitle')
        if title_tag:
            data['title'] = clean_text(title_tag).replace(' - Google Patents', '')

        # 2. Abstract
        abstract_section = soup.find('section', itemprop='abstract')
        if abstract_section:
            abstract_div = abstract_section.find('div', class_='abstract')
            if abstract_div:
                data['abstract'] = clean_text(abstract_div)

        # 3. Classifications
        # Note: Classifications usually don't have sub/sup, but we can stick to get_text or clean_text
        classifications_list = soup.find_all('li', itemprop='classifications')
        for li in classifications_list:
            code_span = li.find('span', itemprop='Code')
            desc_span = li.find('span', itemprop='Description')
            if code_span:
                classification = {
                    'code': clean_text(code_span),
                    'description': clean_text(desc_span) if desc_span else None
                }
                if classification not in data['classifications']:
                    data['classifications'].append(classification)

        # 4. Claims
        claims_section = soup.find('section', itemprop='claims')
        if claims_section:
            claim_tags = claims_section.find_all('claim')
            if not claim_tags:
                claim_divs = claims_section.find_all('div', class_='claim-text')
                for div in claim_divs:
                     data['claims'].append(clean_text(div))
            else:
                for claim_tag in claim_tags:
                    claim_text_div = claim_tag.find('div', class_='claim-text')
                    if claim_text_div:
                        claim_num = claim_tag.get('num')
                        claim_txt = clean_text(claim_text_div)
                        data['claims'].append({
                            'number': claim_num,
                            'text': claim_txt
                        })

        # 5. Extract Additional Metadata
        # Publication Number
        pub_num_tag = soup.find('dd', itemprop='publicationNumber')
        publication_number = clean_text(pub_num_tag) if pub_num_tag else None

        # Country Code
        country_tag = soup.find('dd', itemprop='countryName') 
        if not country_tag:
            country_tag = soup.find('span', itemprop='countryCode')
        country = clean_text(country_tag) if country_tag else None

        # Inventors
        inventors = [clean_text(tag) for tag in soup.find_all('dd', itemprop='inventor')]

        # Assignees
        assignees_current = [clean_text(tag) for tag in soup.find_all('dd', itemprop='assigneeCurrent')]
        assignees_original = [clean_text(tag) for tag in soup.find_all('dd', itemprop='assigneeOriginal')]

        # Events
        events = []
        events_tags = soup.find_all('dd', itemprop='events')
        for event in events_tags:
            date_tag = event.find('time', itemprop='date')
            title_tag = event.find('span', itemprop='title')
            type_tag = event.find('span', itemprop='type')
            
            events.append({
                'date': clean_text(date_tag) if date_tag else None,
                'title': clean_text(title_tag) if title_tag else None,
                'type': clean_text(type_tag) if type_tag else None
            })

        # Status
        # Look for status in "legalStatusIfi", "legalStatus", or "status"
        status_tag = soup.find('span', itemprop='status')
        if not status_tag:
            status_tag = soup.find('span', itemprop='legalStatus')
        status = clean_text(status_tag) if status_tag else "Pending"

        # 6. Description
        description_section = soup.find('section', itemprop='description')
        if description_section:
            paragraphs = description_section.find_all('div', class_='description-paragraph')
            for p in paragraphs:
                text = clean_text(p)
                if text:
                    # Remove [00XX] or [00XXX] markers (with optional internal spaces) anywhere in the text
                    text = re.sub(r'\[\s*\d+\s*\]', '', text).strip()
                    data['description'].append(text)

        # 6. Similar Documents
        similar_docs_rows = soup.find_all('tr', itemprop='similarDocuments')
        for row in similar_docs_rows:
            doc_data = {
                'publication': None,
                'date': None,
                'title': None,
                'link': None
            }
            
            # Publication (could be publicationNumber or scholarAuthors)
            pub_num = row.find('span', itemprop='publicationNumber')
            if pub_num:
                doc_data['publication'] = clean_text(pub_num)
            else:
                authors = row.find('span', itemprop='scholarAuthors')
                if authors:
                    doc_data['publication'] = clean_text(authors)
            
            # Date
            date_time = row.find('time', itemprop='publicationDate')
            if date_time:
                doc_data['date'] = date_time.get_text(strip=True)
                
            # Title
            title_td = row.find('td', itemprop='title')
            if title_td:
                doc_data['title'] = clean_text(title_td)
                
            # Link
            link_tag = row.find('a')
            if link_tag and link_tag.has_attr('href'):
                href = link_tag['href']
                if href.startswith('/'):
                    href = f"https://patents.google.com{href}"
                doc_data['link'] = href
                
            data['similar_documents'].append(doc_data)
        
        data['publication_number'] = publication_number
        data['country'] = country
        data['inventors'] = inventors
        data['assignees']['current'] = assignees_current
        data['assignees']['original'] = assignees_original
        data['events'] = events
        data['status'] = status

    except Exception as e:
        print(f"Error during parsing: {e}", file=sys.stderr)
        # We return whatever data we have collected so far

    return data

def main():
    parser = argparse.ArgumentParser(description='Scrape Google Patent data.')
    parser.add_argument('url', help='The URL of the Google Patent to scrape')
    parser.add_argument('--output', '-o', help='Output JSON file path', default=None)
    
    args = parser.parse_args()
    
    result = scrape_patent(args.url)
    
    if result:
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved data to {args.output}")
        else:
            # Print to stdout
            print(json.dumps(result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
