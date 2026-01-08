
import pandas as pd
import os

def debug_categories():
    base_dir = os.getcwd()
    csv_path = os.path.join(base_dir, "planning", "IPscore-full-table.csv")
    print(f"Reading CSV from: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows.")
        
        categories_map = {
            'A': 'Legal Status',
            'B': 'Technology',
            'C': 'Market Conditions',
            'D': 'Finance',
            'E': 'Strategy'
        }
        
        qs = []
        for index, row in df.iterrows():
            if pd.isna(row['Factor']) or not str(row['Factor']).strip():
                continue
            
            f_code = str(row['Factor']).strip()
            if not f_code: continue
            
            c_code = f_code[0]
            cat_name = categories_map.get(c_code, "Other")
            qs.append(cat_name)
            
            # Print potentially weird Finance entries
            if "Finance" in cat_name:
                print(f"Found Finance via Code: '{f_code}' -> '{cat_name}'")
            
        unique_cats = sorted(list(set(qs)))
        print(f"\nUnique Categories List (Sorted): {unique_cats}")
        print(f"List Length: {len(unique_cats)}")
        
    except Exception as e:
        print(f"Error reading CSV: {e}")

if __name__ == "__main__":
    debug_categories()
