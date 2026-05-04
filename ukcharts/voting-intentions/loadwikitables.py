
import pandas as pd
import requests
import sys
import io
from io import  StringIO
import shutil
from pathlib import Path

url = "https://en.wikipedia.org/wiki/Opinion_polling_for_the_next_United_Kingdom_general_election"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

response = requests.get(url, headers=headers)
response.raise_for_status()
        
html_content = StringIO(response.text)
        
tables = pd.read_html(html_content, flavor='lxml')

if not tables:
    print("No tables were found on the page.")



def clean_data(df):
    # The html table has a two line header which is not correct for dataframes
    # this seems to prevent normal operations on the data frame, so save it as a csv, reload ir and delete the first row
    df.to_csv('temp.csv', index=False)
    df1 = pd.read_csv("temp.csv")
    df1 = df1.tail(-1)
    
    # To remove 'note' rows change a col to numeric. Notes will be strings which convert to None
    # then drop the rows with None thus removing the notes
    df1['Sample size'] = pd.to_numeric(df1['Sample size'],errors='coerce')
    df1 = df1.dropna(subset=['Sample size']) # remove 'note' rows
    
    # Rename abbreviations
    df1 = df1.rename(columns={
        'Con': 'Conservative',
        'Lab': 'Labour',
        'LD': 'Liberal Democrats',
        'Grn': 'Green',
        'Ref': 'Reform',
        'PC': 'Plaid Cymru'
    }, errors="raise")
    
    # Convert party columns to numeric. Replace '-' with None, replace '%' 
    party_cols = ['Conservative', 'Labour', 'Liberal Democrats', 'Green', 'Reform', 'SNP', 'Plaid Cymru', 'Others']
    df1[party_cols]= (   
        df1[party_cols].replace(r"–", None, regex=True)
    )
    df1[party_cols] = (
        df1[party_cols].replace(r"%","", regex=True)
    )
    
    # Remove the refs from the Pollsters name, e.g. 'Ipsos[2]' becomes simply 'Ipsos'
    df1['Pollster'] = df1['Pollster'].str.replace(r'\[[A-Za-z0-9]+\]', '', regex=True)
    df1['Pollster'] = df1['Pollster'].str.replace(r' \(MRP\)', '', regex=True)
    # JL Partners is sometimes styled J.L. Partners
    df1['Pollster'] = df1['Pollster'].str.replace('J.L.', 'JL')
    
    df1['Pollster'] = df1['Pollster'].str.strip()
    return df1


def parse_start_date(s, year):
    s = str(s).replace("–", "-")   # normalize dash
    #print(#s)
    
    if s.find("-")>-1: 
        start = s.split("-")[1].strip()
        #print("startwith-",s, start)
    else:
        start = s.strip()
        #print("startwithout-",s, start)
    
    d = pd.to_datetime(f"{start} {year}", dayfirst=True)
    #print(d)
    return d






table = 1
year = "2026"

df = tables[table]
#
df.head()

df1 = clean_data(df)
df1["Date"] = df1["Date(s) conducted"].apply(parse_start_date, year=year)

df1.to_csv(f"{year}.csv", index=False)


df1.head()


table = 2
year = "2025"

df = tables[table]

df2 = clean_data(df)
df2["Date"] = df2["Date(s) conducted"].apply(parse_start_date, year=year)

df2.to_csv(f"{year}.csv", index=False)
df2.head()


dfAll = pd.concat([df1,df2])
dfAll.to_csv(f"all.csv", index=False)




dfAll.head()



# 1. Get the latest date
latest_date = dfAll['Date'].max()

# 2. Calculate one year before
one_year_before = latest_date - pd.DateOffset(years=1)

# 3. Filter dataframe for the last year
#ytod = dfAll[dfAll['Date'] >= one_year_before]
ytod = dfAll[(dfAll['Date'] >= one_year_before) & (dfAll['Date'] <= latest_date)]

print("Latest date:", latest_date)
print("One year before:", one_year_before)
print("Filtered min:", ytod['Date'].min())
print("Filtered max:", ytod['Date'].max())
print(ytod[-1:]['Date'])

ytod.to_csv(f"ytod.csv", index=False)

# Auto-deploy to app data directory
def deploy_data(source_file="ytod.csv"):
    """Copy data file to app data directory after successful generation."""
    project_root = Path(__file__).parent.parent
    dest = project_root / "data" / "ytod.csv"

    src = Path(source_file)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # Validate source has data
    df = pd.read_csv(src)
    if df.empty:
        raise ValueError("Generated data is empty!")

    # Copy to destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"✓ Deployed {len(df)} rows to {dest}")
    print("⚠️  Remember to restart the Flask app to clear data caches!")

#deploy_data()
