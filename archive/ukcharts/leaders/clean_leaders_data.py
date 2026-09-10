
import pandas as pd
import re
from datetime import datetime

def clean_leaders_data(input_file, output_file):
    # Read the first few lines to find the headers
    raw_headers = pd.read_csv(input_file, header=None, nrows=1).iloc[0].tolist()
    
    # Read the raw CSV skipping messy headers
    df = pd.read_csv(input_file, header=None, skiprows=3)
    
    # Define columns dynamically
    cols = ['date', 'pollster', 'sample_size']
    
    # The leaders/parties start from index 3 in triplets
    leader_names = []
    for i in range(3, len(raw_headers), 3):
        name = str(raw_headers[i]).strip()
        # Map party names to leader names if necessary
        mapping = {
            'Labour': 'Keir Starmer',
            'Conservative': 'Kemi Badenoch',
            'Reform': 'Nigel Farage',
            'Lib Dems': 'Ed Davey',
            'Green': 'Zack Polanski',
            'Your': 'Rupert Lowe',
            'Restore': 'Restore Britain'
        }
        leader_name = mapping.get(name, name)
        leader_names.append(leader_name)
        cols.extend([f"{leader_name}_Pos", f"{leader_name}_Neg", f"{leader_name}_Net"])
    
    # Assign columns
    df.columns = cols[:len(df.columns)]
    
    # 1. Filter out junk rows (where sample_size is not a number)
    df['sample_size'] = pd.to_numeric(df['sample_size'], errors='coerce')
    df = df.dropna(subset=['sample_size'])
    
    # 2. Clean citations [123] and [a] from Pollster and Date
    def remove_citations(text):
        if not isinstance(text, str): return text
        # Remove [123] or [a]
        text = re.sub(r'\[.*?\]', '', text)
        # Remove "Archived ..." at the end
        text = re.sub(r'Archived.*$', '', text)
        return text.strip()
    
    df['pollster'] = df['pollster'].apply(remove_citations)
    df['date_raw'] = df['date'].apply(remove_citations)
    
    # 3. Parse Dates
    # Format: "24–27 Apr 2026" or "27 Feb – 2 Mar 2026"
    def parse_wikipedia_date(date_str):
        try:
            # Clean en-dash to hyphen
            date_str = date_str.replace('–', '-').replace('—', '-')
            
            # Extract the part after the hyphen if it exists (the end date)
            if '-' in date_str:
                parts = date_str.split('-')
                end_part = parts[-1].strip()
                # If end_part is just a number (e.g. "27" in "24-27 Apr 2026"), 
                # we need the month and year from the original string
                if end_part.isdigit():
                    month_year = re.search(r'[a-zA-Z]+\s+\d{4}', date_str).group()
                    end_date_str = f"{end_part} {month_year}"
                else:
                    end_date_str = end_part
            else:
                end_date_str = date_str.strip()
            
            return pd.to_datetime(end_date_str, errors='coerce')
        except:
            return pd.NaT

    df['date'] = df['date_raw'].apply(parse_wikipedia_date)
    df = df.dropna(subset=['date'])
    
    # 4. Clean Numeric Columns
    for col in df.columns:
        if '_Pos' in col or '_Neg' in col or '_Net' in col:
            # Replace en-dash with minus, remove %, convert to numeric
            df[col] = df[col].astype(str).str.replace('–', '-').str.replace('%', '').str.replace('+', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 5. Reshape to Long Format (Tidy Data)
    # We want: date, pollster, sample_size, Leader, Pos, Neg, Net
    id_vars = ['date', 'pollster', 'sample_size']
    
    # Split into a list of dataframes per leader and concat
    leader_dfs = []
    for leader in leader_names:
        leader_cols = [f"{leader}_Pos", f"{leader}_Neg", f"{leader}_Net"]
        # Check if these columns exist in the dataframe
        if all(c in df.columns for c in leader_cols):
            temp_df = df[id_vars + leader_cols].copy()
            temp_df.columns = id_vars + ['Pos', 'Neg', 'Net']
            temp_df['Leader'] = leader
            leader_dfs.append(temp_df)
    
    tidy_df = pd.concat(leader_dfs, ignore_index=True)
    
    # Remove rows with no data for a leader
    tidy_df = tidy_df.dropna(subset=['Pos', 'Neg', 'Net'], how='all')
    
    # Sort by date
    tidy_df = tidy_df.sort_values('date')
    
    # Save to CSV
    tidy_df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")
    return tidy_df

if __name__ == "__main__":
    clean_leaders_data('leaderstemp.csv', 'leaders_cleaned.csv')
