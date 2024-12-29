import sqlite3
from flask import jsonify

# Example database path (use your actual database location)
dbLocation = 'stockDB.db'

def list_stocks(db_path=dbLocation):
    # Fetch stock tickers from portfolio transactions
    stock_query = """
    SELECT DISTINCT Stocks.ticker, Stocks.id 
    FROM portfolioTransactions 
    JOIN Stocks ON portfolioTransactions.tickerid = Stocks.id;
    """
    
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    cursor.execute(stock_query)
    stocks = cursor.fetchall()  # [(ticker, stock_id), ...]
    connection.close()
    return stocks

def list_industries(db_path=dbLocation):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT i.id AS IndustryID, i.yahooname AS YahooName, COUNT(s.id) AS StockCount FROM industries i LEFT JOIN Stocks s ON i.id = s.industryID GROUP BY i.id, i.yahooname ORDER BY StockCount DESC;"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    industries = []
    for row in data:
        industries.append({
            'industryID': row[0],
            'yahooname': row[1],
            'stockCount': row[2]
        })
    return industries

def get_stock_by_industry(industry_id, db_path=dbLocation):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT ticker, stockname, exchange FROM Stocks WHERE industryID = ?"
    cursor.execute(query, (industry_id,))
    data = cursor.fetchall()
    conn.close()

    stocks = []
    for row in data:
        stocks.append({
            'ticker': row[0],
            'stockname': row[1],
            'exchange': row[2]
        })
    return stocks

def get_latest_economic_data(db_path='stockDB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM economyhistory ORDER BY date DESC LIMIT 1;"
    cursor.execute(query)
    data = cursor.fetchone()
    conn.close()
    
    if data:
        return {
            'inflation': data[2],
            'ECBInterest': data[3],
            'NL_Unemployment': data[4],
            'NL_ConsumerConfidence': data[5],
            'EUR_USD_ExchangeRate': data[6],
            'NL_RetailSales': data[7],
            'NL_GDPGrowth': data[8],
            'NL_IndustrialProduction': data[9],
            'NL_Bankrupcies': data[10],
        }
    return {}
    
def smoothenEconomicData(economic_data):
    """
    Processes and smoothens the economic data.
    - Adds '%' symbol to percentage values.
    - Rounds currency exchange rates.
    - Renames keys for better readability.
    """
    # Round EUR/USD exchange rate to two decimal places
    if 'EUR_USD_ExchangeRate' in economic_data:
        economic_data['EUR_USD_ExchangeRate'] = round(economic_data['EUR_USD_ExchangeRate'], 2)

    # Append '%' to relevant percentage values
    percent_keys = [
        'inflation', 'ECBInterest', 'NL_Unemployment', 
        'NL_RetailSales', 'NL_GDPGrowth', 'NL_IndustrialProduction', 'NL_Bankrupcies'
    ]
    for key in percent_keys:
        if key in economic_data:
            economic_data[key] = f"{economic_data[key]}%"

    # Rename keys to make them more readable
    economic_data = {
        key.replace("_", " ").capitalize(): value
        for key, value in economic_data.items()
    }

    # Return the processed economic data
    return format_economic_data(economic_data)

def format_economic_data(data):
    formatted_data = {}

    icon_and_color_mapping = {
        "NL Consumer Confidence": {"icon": "fa-chart-line", "color": "blue"},
        "NL bankrupcies": {"icon": "fa-building", "color": "cyan"},
        "NL Industrial Production": {"icon": "fa-industry", "color": "green"},
        "ECB Interest": {"icon": "fa-euro-sign", "color": "purple"},
        "NL Unemployment": {"icon": "fa-user-slash", "color": "orange"},
        "NL retailsales": {"icon": "fa-chart-line", "color": "yellow"},
        "Inflation": {"icon": "fa-chart-pie", "color": "red"},
        "NL gdpgrowth": {"icon": "fa-arrow-up", "color": "teal"},
        "Eur usd exchangerate": {"icon": "fa-home", "color": "pink"},   
    }

    # Format the economic data
    for key, value in data.items():
        # Ensure we handle mixed case keys by converting them to lowercase
        formatted_key = key.replace("_", "")  # Remove underscores and make lowercase
        formatted_key = formatted_key.replace("Nl","NL")
        formatted_key = formatted_key.replace("consumerconfidence","Consumer Confidence")
        formatted_key = formatted_key.replace("industrialproduction","Industrial Production")
        formatted_key = formatted_key.replace("Ecbinterest","ECB Interest")
        formatted_key = formatted_key.replace("unemployment","Unemployment")
        formatted_key = formatted_key.replace("consumerconfidenceNL","NL Consumer Confidence")


        
        # Format values for long text (if applicable)
        if isinstance(value, str) and len(value) > 20:  # If value is too long
            value = value[:17] + '...'  # Limit length for better readability

        # Assign color and icon from the mapping
        if formatted_key in icon_and_color_mapping:
            formatted_data[formatted_key] = {
                'color': icon_and_color_mapping[formatted_key]['color'],
                'icon': icon_and_color_mapping[formatted_key]['icon'],
                'value': value
            }
        else:
            # Default fallback for unknown keys
            formatted_data[formatted_key] = {
                'color': 'gray',  # Default color
                'icon': 'fa-question-circle',  # Default icon
                'value': value
            }
    return formatted_data


def get_all_profiles(dbLocation):
    db_location = dbLocation  # Replace with your actual database location
    conn = sqlite3.connect(db_location)
    cursor = conn.cursor()

    query = "SELECT id, name FROM ProfileConfiguration"  # Adjust table/column names as per your schema
    cursor.execute(query)
    profiles = cursor.fetchall()

    conn.close()

    # Convert to a list of dictionaries for easier use in templates
    return [{"id": profile[0], "name": profile[1]} for profile in profiles]


def generate_watchlist(profile, easeFactor, dbLocation):
    conn = sqlite3.connect(dbLocation)
    cursor = conn.cursor()

    query = """
        SELECT 
            s.id, s.ticker, s.stockname, s.Exchange, 
            sh.beta, sh.peratio, sh.pbratio, sh.icr, sh.currentRatio, 
            sh.dividentYield, sh.RandDExpense, sh.revenue, 
            sh.percentageMakingProfitLastFiveYears, si.yahooname
        FROM Stocks s
        JOIN stockhistory sh ON s.id = sh.stockID
        JOIN industries si ON si.id = s.industryID
        WHERE sh.date = (
            SELECT MAX(date)
            FROM stockhistory sh2
            WHERE sh2.stockID = s.id
        )
    """
    cursor.execute(query)
    stocks = cursor.fetchall()

    columns = [
        "id", "ticker", "stockname", "Exchange",
        "beta", "peratio", "pbratio", "icr", "currentRatio",
        "dividentYield", "RandDExpense", "revenue",
        "percentageMakingProfitLastFiveYears", "industry"
    ]
    valid_stocks = []

    def is_good(value, bounds):
        if value is None:
            return False
        lower, upper, direction, red_flag = bounds
        if direction == 'D':
            if red_flag is not None and value > red_flag:
                return False
            return value < lower * easeFactor
        elif direction == 'U':
            if red_flag is not None and value > red_flag:
                return False
            return value > upper / easeFactor

    for stock in stocks:
        stock_data = dict(zip(columns, stock))
        try:
            if stock_data["revenue"] and stock_data["RandDExpense"]:
                stock_data["percRandD"] = (stock_data["RandDExpense"] / stock_data["revenue"]) * 100
            else:
                stock_data["percRandD"] = None
                
            meets_criteria = all([
                stock_data.get("beta") is not None and is_good(stock_data["beta"], profile["beta"]),
                stock_data.get("peratio") is not None and is_good(stock_data["peratio"], profile["peRatio"]),
                stock_data.get("pbratio") is not None and is_good(stock_data["pbratio"], profile["pbRatio"]),
                stock_data.get("icr") is not None and is_good(stock_data["icr"], profile["icr"]),
                stock_data.get("currentRatio") is not None and is_good(stock_data["currentRatio"], profile["currentRatio"]),
                stock_data.get("dividentYield") is not None and is_good(stock_data["dividentYield"], profile["dividendYield"]),
                stock_data.get("percRandD") is not None and is_good(stock_data["percRandD"], profile["percRandD"]),
                stock_data.get("percentageMakingProfitLastFiveYears") is not None and is_good(stock_data["percentageMakingProfitLastFiveYears"], profile["percentageMakingProfitLastFiveYears"]),
          
 ])
            if meets_criteria:
                valid_stocks.append(stock_data)
        except Exception as e:
            print(f"Error processing stock {stock}: {e}")

    conn.close()
    return valid_stocks


    
def get_industry_benchmark_data(industry_id, database_path=dbLocation):

    # Step 1: Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Step 2: Query the industryBenchmark table for the specific industry ID
    cursor.execute("""
        SELECT 
            price, beta, peratio, pbratio, icr, currentRatio, dividentYield, 
            percRandD, lastReturn, fiveYearAverageReturn, percentageMakingProfitLastFiveYears
        FROM industryBenchmark
        WHERE industryID = ?
    """, (industry_id,))
    
    benchmark_data = cursor.fetchone()
    
    # Step 3: Check if data exists for this industry, and return it in a dictionary
    if benchmark_data:
        benchmark_dict = {
            "price": benchmark_data[0],
            "beta": round(benchmark_data[1], 2) if benchmark_data[1] is not None else None,
            "peratio": round(benchmark_data[2], 2) if benchmark_data[2] is not None else None,
            "pbratio": round(benchmark_data[3], 2) if benchmark_data[3] is not None else None,
            "icr": round(benchmark_data[4], 2) if benchmark_data[4] is not None else None,
            "currentRatio": round(benchmark_data[5], 2) if benchmark_data[5] is not None else None,
            "dividentYield": round(benchmark_data[6], 2) if benchmark_data[6] is not None else None,
            "percRandD": round(benchmark_data[7], 2) if benchmark_data[7] is not None else None,
            "lastReturn": round(benchmark_data[8], 2) if benchmark_data[8] is not None else None,
            "fiveYearAverageReturn": round(benchmark_data[9], 2) if benchmark_data[9] is not None else None,
            "percentageMakingProfitLastFiveYears": round(benchmark_data[10], 2) if benchmark_data[10] is not None else None,
        }
    else:
        benchmark_dict = {}  # Return an empty dictionary if no data is found
    
    # Step 4: Close the connection
    conn.close()
    
    return benchmark_dict
    
def get_stock_data(ticker, db_path=dbLocation):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    try:
        # Fetch stock's general info
        stock_query = """
        SELECT s.ticker, s.stockname, s.Exchange, si.name, se.sector, MAX(sh.date), sh.price, sh.operatingIncom, sh.currentRatio,
               sh.icr, sh.pbratio, sh.peratio, sh.beta, sh.fiveYearAverageReturn, sh.lastReturn, sh.dividentYield, sh.revenue,
               sh.RandDExpense, sh.currency, sh.percentageMakingProfitLastFiveYears, si.id
        FROM Stocks s
        JOIN Sectors se ON s.sectorID = se.id
        JOIN industries si on s.industryID = si.id
        JOIN stockhistory sh ON s.id = sh.stockID
        WHERE s.ticker = ?
        GROUP BY s.ticker
        ORDER BY MAX(sh.date) DESC
        LIMIT 1
        """
        cursor.execute(stock_query, (ticker,))
        result = cursor.fetchone()
        
        if not result:
            print(f"No data found for ticker: {ticker}")
            return None
        
        columns = [
            "ticker", "stockname", "Exchange", "industry", "sector", "date", "price", "operatingIncome",
            "currentRatio", "icr", "pbRatio", "peRatio", "beta", "fiveYearAvgReturn",
            "lastReturn", "dividendYield", "revenue", "rAndDExpense", "currency", "percentageMakingProfitLastFiveYears","industryID"
        ]
        return enrich_stock_data(dict(zip(columns, result)))
    
    finally:
        connection.close()

def enrich_stock_data(stock_data):
    if not stock_data:
        print("No stock data provided for enrichment.")
        return None

    # Safely retrieve and process revenue and R&D expense, defaulting to 0 if not available
    revenue = stock_data.get("revenue", 0) or 0
    rAndDExpense = stock_data.get("rAndDExpense", 0) or 0
    operatingIncome = stock_data.get("operatingIncome", 0) or 0

    # Calculate percRandD, ensuring no division by zero
    percRandD = round(((rAndDExpense / revenue)*100),2) if revenue else 0

    # Convert values to millions
    stock_data["revenue"] = revenue / 1_000_000
    stock_data["rAndDExpense"] = rAndDExpense / 1_000_000
    stock_data["operatingIncome"] = operatingIncome / 1_000_000

    # Add the percRandD field to the stock data
    stock_data["percRandD"] = percRandD

    return stock_data

def generateVerdicts(stock_data, profile):
    verdicts = {}
    verdicts['percRandD'] = verdict('percRandD', stock_data['percRandD'], profile)
    verdicts['percentageMakingProfitLastFiveYears'] = verdict('percentageMakingProfitLastFiveYears', stock_data['percentageMakingProfitLastFiveYears'], profile)
    verdicts['icr'] = verdict('icr', stock_data['icr'], profile )
    verdicts['currentRatio'] = verdict('currentRatio', stock_data['currentRatio'], profile)
    verdicts['beta'] = verdict('beta', stock_data['beta'], profile)
    verdicts['dividendYield'] = verdict('dividendYield', stock_data['dividendYield'], profile)
    verdicts['peRatio'] = verdict('peRatio', stock_data['peRatio'], profile)
    verdicts['pbRatio'] = verdict('pbRatio', stock_data['pbRatio'], profile)
    return verdicts    
        
def verdict(parameter, value, profile):
    # Colors
    GREEN = '#2ecc71'  # Green
    YELLOW = '#f39c12'  # Yellow
    RED = '#e74c3c'  # Red
    
    # Smiley icons
    SMILEY_GREEN = '<i class="fas fa-smile" style="color: {}; font-size: 20px;"></i>'
    SMILEY_YELLOW = '<i class="fas fa-meh" style="color: {}; font-size: 20px;"></i>'
    SMILEY_RED = '<i class="fas fa-frown" style="color: {}; font-size: 20px;"></i>'

    # Extract the parameter profile details
    lower_bound, upper_bound, direction, exception = profile[parameter]
    
    # Initialize smiley variable
    smiley = ''
    
    # Determine the verdict based on the logic
    if direction == 'D':  # Downward logic
        if value < lower_bound:  # Below lower bound
            smiley = SMILEY_GREEN.format(GREEN)
        elif lower_bound <= value <= upper_bound:  # Within range
            smiley = SMILEY_YELLOW.format(YELLOW)
        else:  # Above upper bound
            smiley = SMILEY_RED.format(RED)
        # Check the exception threshold if it exists
        if exception is not None and value < exception:
            smiley = SMILEY_RED.format(RED)

    elif direction == 'U':  # Upward logic
        if value < lower_bound:  # Below lower bound
            smiley = SMILEY_RED.format(RED)
        elif lower_bound <= value <= upper_bound:  # Within range
            smiley = SMILEY_YELLOW.format(YELLOW)
        else:  # Above upper bound
            smiley = SMILEY_GREEN.format(GREEN)
        # Check the exception threshold if it exists
        if exception is not None and value > exception:
            smiley = SMILEY_RED.format(RED)

    return smiley  # Return the smiley HTML


def get_dividents(database_path=dbLocation):
    # Establish connection to the database
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    
    # Query to fetch dividend records along with stock tickers
    query = """
    SELECT Stocks.ticker, dividends.id, dividends.date, dividends.dividendPerShare
    FROM dividends
    JOIN Stocks ON dividends.stockID = Stocks.id
    """
    
    # Execute the query and fetch all results
    cursor.execute(query)
    dividends = cursor.fetchall()
    
    # Close the connection
    connection.close()
    
    # Return the results as a list of tuples
    return dividends

def insert_dividend(myRequest, database_path=dbLocation):
    stock_id = myRequest.form.get('stock_id')
    record_date = myRequest.form.get('record_date')
    dividend_per_share = myRequest.form.get('dividend_per_share')

    # Insert the dividend record into the database
    insert_query = """
    INSERT INTO dividends (stockID, date, dividendPerShare)
    VALUES (?, ?, ?);
    """
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    cursor.execute(insert_query, (stock_id, record_date, dividend_per_share))
    connection.commit()
    connection.close()
    
def insert_dividend_expectation(myRequest, database_path=dbLocation):
    stock_id = myRequest.form['stock_id']
    month = myRequest.form['month']
    expected_dividend = myRequest.form['expected_dividend']

    # Insert the dividend expectation into the database
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    query = """
        INSERT INTO dividendExpectations (stockID, expectedMonth, expectedDividendPerShare)
        VALUES (?, ?, ?)
    """
    cursor.execute(query, (stock_id, month, expected_dividend))
    connection.commit()
    connection.close()
    
def insert_transaction(myRequest, database_path=dbLocation):
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    
    # Get the ticker from the request
    ticker = myRequest.form['ticker']
    date = myRequest.form['date']
    quantity = int(myRequest.form['quantity'])
    currency = myRequest.form['currency']
    stock_price = float(myRequest.form['stock_price'])
    transaction_type = myRequest.form['type']
    transaction_fee = float(myRequest.form['transaction_fee'])

    # Look up stockID for the given ticker
    stock_id_query = "SELECT id FROM Stocks WHERE ticker = ?"
    cursor.execute(stock_id_query, (ticker,))
    stock_id_result = cursor.fetchone()
    
    if not stock_id_result:
        # Ticker not found in the Stocks table
        connection.close()
        raise ValueError(f"Ticker '{ticker}' not found in the Stocks table.")

    # Extract stockID from the query result
    ticker_id = stock_id_result[0]

    # Insert the transaction into the portfolioTransactions table
    query = """
    INSERT INTO portfolioTransactions (tickerid, date, quantity, currency, stockPrice, Type, transactionFee)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (ticker_id, date, quantity, currency, stock_price, transaction_type, transaction_fee))
    connection.commit()
    connection.close()

def delete_dividend(dividend_id, database_path=dbLocation):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    query = "DELETE FROM dividends WHERE id = ?"
    print(dividend_id)
    cursor.execute(query, (dividend_id,))
    connection.commit()
    connection.close()

def delete_transaction(transaction_id, database_path=dbLocation):
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    query = "DELETE FROM portfolioTransactions WHERE id = ?"
    cursor.execute(query, (transaction_id,))
    connection.commit()
    connection.close()
    
def get_all_transactions(database_path=dbLocation):
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    
    query = """
    SELECT
        portfolioTransactions.id,
        portfolioTransactions.tickerid,
        Stocks.ticker,
        Stocks.stockname,
        portfolioTransactions.date,
        portfolioTransactions.quantity,
        portfolioTransactions.currency,
        portfolioTransactions.stockPrice,
        portfolioTransactions.Type,
        portfolioTransactions.transactionFee
    FROM portfolioTransactions
    JOIN Stocks ON portfolioTransactions.tickerid = Stocks.id;
    """
    
    transactions = cursor.execute(query).fetchall()
    connection.close()
    
    return transactions

def delete_dividend_expectation(expectation_id):
    # Delete dividend expectation from the database
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    query = "DELETE FROM dividendExpectations WHERE id = ?"
    cursor.execute(query, (expectation_id,))
    connection.commit()
    connection.close()


def get_dividend_expectations(dbLocation):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    query = """
    SELECT 
        Stocks.ticker,
        dividendExpectations.stockID,
        dividendExpectations.expectedMonth,
        dividendExpectations.expectedDividendPerShare,
        dividendExpectations.id
    FROM 
        dividendExpectations
    JOIN 
        Stocks
    ON 
        dividendExpectations.stockID = Stocks.id
    """
    cursor.execute(query)
    expectations = cursor.fetchall()
    connection.close()
    return expectations

    
    
def calculate_dividend_expectations(database_path=dbLocation):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row  # Enables dictionary-like access
    cursor = connection.cursor()
    query = """
    SELECT
        expectedMonth,
        SUM(expectedDividendPerShare * portfolioTransactions.quantity) AS totalExpectedPayment
    FROM dividendExpectations
    JOIN portfolioTransactions ON dividendExpectations.stockID = portfolioTransactions.tickerid
    GROUP BY expectedMonth
    ORDER BY CASE
        WHEN expectedMonth = 'Jan' THEN 1
        WHEN expectedMonth = 'Feb' THEN 2
        WHEN expectedMonth = 'Mar' THEN 3
        WHEN expectedMonth = 'Apr' THEN 4
        WHEN expectedMonth = 'May' THEN 5
        WHEN expectedMonth = 'Jun' THEN 6
        WHEN expectedMonth = 'Jul' THEN 7
        WHEN expectedMonth = 'Aug' THEN 8
        WHEN expectedMonth = 'Sep' THEN 9
        WHEN expectedMonth = 'Oct' THEN 10
        WHEN expectedMonth = 'Nov' THEN 11
        WHEN expectedMonth = 'Dec' THEN 12
    END;
    """
    cursor.execute(query)
    sqlresult = cursor.fetchall()
    connection.close()

    result = {"January":0,"February":0,"March":0,"April":0,"May":0,"June":0,"July":0,"August":0,"September":0,"October":0,"November":0,"December":0,}
    
    for row in sqlresult:
        result[row['expectedMonth']] = row['totalExpectedPayment']

    return result







########################################################################

def calculate_dividends(cursor, stock_id):
    # Fetch portfolio transactions for the stock
    cursor.execute("""
        SELECT id, date, quantity, stockPrice, Type, currency
        FROM portfolioTransactions
        WHERE tickerid = ?
        ORDER BY date
    """, (stock_id,))
    transactions = cursor.fetchall()

    # Fetch dividends for the stock
    cursor.execute("""
        SELECT date, dividendPerShare
        FROM dividends
        WHERE stockID = ?
        ORDER BY date
    """, (stock_id,))
    dividends = cursor.fetchall()
    
    total_dividends = 0
    for txn in transactions:
        txn_id, txn_date, txn_quantity, txn_price, txn_type, txn_currency = txn
        for div in dividends:            
            div_date, div_per_share = div
            if txn_date <= div_date:
                if(txn_type == 'Buy'):
                    total_dividends += txn_quantity * div_per_share
                else:
                    total_dividends -= txn_quantity * div_per_share
    return total_dividends

def get_portfolio_data(database_path=dbLocation):
    connection = sqlite3.connect(database_path)
    # Enable access to columns by name
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    # Get latest exchange rate
    exchange_rate_query = "SELECT EUR_USD_ExchangeRate FROM economyhistory ORDER BY date DESC LIMIT 1;"
    exchange_rate = cursor.execute(exchange_rate_query).fetchone()[0]
    
    # Fetch stock data only for stocks in portfolioTransactions
    cursor.execute("""
        SELECT DISTINCT Stocks.id, Stocks.ticker, Stocks.stockname
        FROM Stocks
        JOIN portfolioTransactions ON Stocks.id = portfolioTransactions.tickerid
    """)
    stocks = cursor.fetchall()
    
    portfolio = []
    for stock in stocks:
        stock_id = stock['id']
        
        # Fetch invested and current value
        cursor.execute("""
            SELECT
                Stocks.ticker,
                Stocks.stockname AS full_name,
                portfolioTransactions.currency,
                SUM(CASE 
                    WHEN portfolioTransactions.Type = 'Buy' 
                    THEN (portfolioTransactions.quantity * portfolioTransactions.stockPrice) + portfolioTransactions.transactionFee
                    ELSE -(portfolioTransactions.quantity * portfolioTransactions.stockPrice) - portfolioTransactions.transactionFee
                END) AS invested,
                (SELECT stockhistory.price
                 FROM stockhistory
                 WHERE stockhistory.stockID = Stocks.id
                 ORDER BY stockhistory.date DESC
                 LIMIT 1) AS latest_price,
                SUM(CASE 
                    WHEN portfolioTransactions.Type = 'Buy' 
                    THEN portfolioTransactions.quantity
                    ELSE -portfolioTransactions.quantity
                END) AS quantity,
                portfolioTransactions.currency
            FROM portfolioTransactions
            JOIN Stocks ON portfolioTransactions.tickerid = Stocks.id
            WHERE Stocks.id = ?
            GROUP BY Stocks.id, Stocks.ticker, Stocks.stockname, portfolioTransactions.currency
        """, (stock_id,))
        row = cursor.fetchone()
        
        invested = row['invested']
        current_value = row['latest_price'] * row['quantity']
        dividends = calculate_dividends(cursor, stock_id)
        
        # Adjust for USD currency
        if row['currency'] == 'USD':
            invested /= exchange_rate
            current_value /= exchange_rate
        
        # Calculate return percentage
        total_value = current_value + dividends
        return_percentage = ((total_value - invested) / invested) * 100 if invested else 0
        
        # Append to portfolio list
        portfolio.append({
            "ticker": stock['ticker'],
            "full_name": stock['stockname'],
            "invested": invested,
            "quantity": row['quantity'],
            "current_value": current_value,
            "dividends": dividends,
            "return_percentage": return_percentage
        })
    
    connection.close()
    return portfolio
