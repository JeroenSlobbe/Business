import requests
import pandas as pd
import sqlite3
from datetime import datetime
from io import StringIO

# Step 1: Download the file from the URL
url = "https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_and_NYSE_MKT_Trading_Units_Daily_File.xls"
response = requests.get(url)

if response.status_code == 200:
    print("File downloaded successfully.")
else:
    raise Exception("Failed to download file from NYSE.")

# Step 2: Convert the content to text and load it into pandas
content = response.text

# Step 3: Use pandas to read the text as a tab-separated file
from io import StringIO

# Read the content as a CSV (tab-separated)
df = pd.read_csv(StringIO(content), sep="\t")

# Step 4: Clean up column names by stripping leading/trailing spaces
df.columns = df.columns.str.strip()

# Step 5: Check if the necessary columns exist
print(df.columns)

# Filter the relevant columns and rows, apply the Auction and Tape filter
if 'Company' in df.columns and 'Symbol' in df.columns:
    # Filter by Auction = 'Y' and Tape = 'Tape A'
    filtered_df = df[(df['Auction'] == 'Y') & (df['Tape'] == 'Tape A')]

    # Extract and clean up the relevant columns
    filtered_df = filtered_df[['Company', 'Symbol']]
    filtered_df.rename(columns={'Company': 'stockname', 'Symbol': 'ticker'}, inplace=True)

    # Add additional columns for Exchange, DateAdded, and Status
    filtered_df['Exchange'] = 'XNYS'  # All data is from NYSE
    filtered_df['DateAdded'] = datetime.now().strftime('%Y-%m-%d')
    filtered_df['Status'] = 'active'

    # Step 6: Insert the data into SQLite database

    db_file = 'screeningsDB.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Ensure the table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Stocks (
        id INTEGER PRIMARY KEY,
        ticker TEXT,
        stockname TEXT,
        Exchange TEXT,
        DateAdded TEXT,
        Status TEXT
    );
    """)

    # Insert rows into the table if the ticker doesn't already exist
    for _, row in filtered_df.iterrows():
        cursor.execute("SELECT COUNT(*) FROM Stocks WHERE ticker = ?", (row['ticker'],))
        if cursor.fetchone()[0] == 0:  # If ticker does not exist
            cursor.execute("""
            INSERT INTO Stocks (ticker, stockname, Exchange, DateAdded, Status) 
            VALUES (?, ?, ?, ?, ?)
            """, (row['ticker'], row['stockname'], row['Exchange'], row['DateAdded'], row['Status']))

    # Commit and close the connection
    conn.commit()
    conn.close()

    print("Data successfully inserted into the database (if not duplicate).")
else:
    print("Expected columns 'Company' or 'Symbol' not found in the data.")
