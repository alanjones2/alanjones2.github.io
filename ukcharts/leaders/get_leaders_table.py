import pandas as pd
import requests
import sys
import io
from io import  StringIO
import shutil
from pathlib import Path

from clean_leaders_data import clean_leaders_data

url = "https://en.wikipedia.org/wiki/Leadership_approval_opinion_polling_for_the_next_United_Kingdom_general_election"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

print(f"Fetching data from {url}...")
response = requests.get(url, headers=headers)
response.raise_for_status()
        
html_content = StringIO(response.text)
        
tables = pd.read_html(html_content, flavor='lxml')

if not tables:
    print("No tables were found on the page.")
else:
    # Use table 18 as per original logic
    df = tables[18]
    
    # Save the raw data
    df.to_csv('leaderstemp.csv', index=False)
    print("Raw data saved to leaderstemp.csv")
    
    # Call the cleaning function
    clean_leaders_data('leaderstemp.csv', 'leaders_cleaned.csv')
