import requests
import sqlite3
from datetime import datetime

# Function to fetch data from URL and insert into SQLite database
def fetch_and_process_euronext_data(db_path):
    # Define the current date for the URL
    current_date = datetime.now().strftime("%d/%m/%Y")
    url = f"https://live.euronext.com/en/pd_es/data/stocks/download?mics=dm_all_stock&market=06%2C07&initialLetter=&fe_type=txt&fe_decimal_separator=&fe_date_format=d%2Fm%2FY&date={current_date}"
    
    # Define exchange mapping
    exchange_mapping = {
        "Euronext Amsterdam": "XAMS",
        "Euronext Brussels": "XBRU"
    }
    
    # Fetch the data
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request failed
    data_lines = response.text.splitlines()  # Split the response into lines

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Process each line
    for line in data_lines:
        # Remove quotes and split by delimiter (;)
        data = line.strip().replace('"', '').split(';')
        
        # Ensure the line has enough data fields
        if len(data) < 4:
            continue
        
        # Extract relevant fields
        stock_name = data[0]
        ticker = data[2]
        exchange_full = data[3]
        exchange = exchange_mapping.get(exchange_full)  # Map exchange name to XAMS/XBRU

        # Skip lines for exchanges other than XAMS or XBRU
        if not exchange:
            continue

        # Check if this ticker is already in the database (avoid duplicates)
        cursor.execute('SELECT COUNT(*) FROM Stocks WHERE ticker = ? AND Exchange = ?', (ticker, exchange))
        if cursor.fetchone()[0] > 0:
            continue

        # Insert only the preferred exchange (XAMS > XBRU)
        if exchange == "XBRU":
            cursor.execute('SELECT COUNT(*) FROM Stocks WHERE ticker = ? AND Exchange = "XAMS"', (ticker,))
            if cursor.fetchone()[0] > 0:
                continue

        # Add the current date
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert the data into the SQLite table
        cursor.execute('''
            INSERT INTO Stocks (ticker, stockname, Exchange, DateAdded, Status)
            VALUES (?, ?, ?, ?, ?)
        ''', (ticker, stock_name, exchange, date_added, 'active'))

    # Commit the transaction and close the database connection
    conn.commit()
    conn.close()

# Example usage
fetch_and_process_euronext_data("screeningsDB.db")
