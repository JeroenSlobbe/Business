import argparse
import sqlite3
from datetime import datetime
from tabulate import tabulate

dbLocation = "ScreeningsDB.db"

def format_currency(value, currency="EUR", scale=1, decimals=2):
    if value is None:
        return "N/A"
    symbol = "€" if currency == "EUR" else "$" if currency == "USD" else ""
    return f"{symbol} {round((value / scale),decimals)}"

def format_percentage(value):
    if value is None:
        return "N/A"
    return f"{value:.2f} %"

def format_benchmark(value):
    bvalue = '\033[35m' + str(value) + '\033[0m' 
    return bvalue

def list_industries(db_path=dbLocation):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT i.id AS IndustryID, i.yahooname AS YahooName, COUNT(s.id) AS StockCount FROM industries i LEFT JOIN Stocks s ON i.id = s.industryID GROUP BY i.id, i.yahooname ORDER BY StockCount DESC;"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Create table
    headers = ["ID", "Yahoo Name", "Stock Count"]
    table = tabulate(data, headers=headers, tablefmt="pretty")
    print(table)

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
        return dict(zip(columns, result))
    
    finally:
        connection.close()

def list_stocks_in_industry(industryID, db_path="ScreeningsDB.db"):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL query to fetch active stocks and the industry name
    query = "SELECT s.id AS StockID, s.ticker AS Ticker, s.stockname AS StockName, s.Exchange AS Exchange FROM Stocks s WHERE s.industryID = ? AND s.Status = 'active' ORDER BY s.stockname;  -- Order by stock name"

    # Execute the query with the industryID parameter
    cursor.execute(query, (industryID,))
    stocks = cursor.fetchall()

    # If no stocks are found, display a message
    if not stocks:
        print(f"No active stocks found for industryID: {industryID}")
    else:
        # Fetch industry name using a separate query
        cursor.execute("SELECT name FROM industries WHERE id = ?", (industryID,))
        industry_name = cursor.fetchone()[0]

        # Print the industry name in the header
        print(f"\nActive Stocks in Industry {industryID} ({industry_name}):")
        print("=" * 50)

        # Table headers
        headers = ["StockID", "Ticker", "StockName", "Exchange"]
        
        # Print formatted table using tabulate
        print(tabulate(stocks, headers=headers, tablefmt="pretty"))

    # Close the database connection
    conn.close()

    
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
            "beta": benchmark_data[1],
            "peratio": benchmark_data[2],
            "pbratio": benchmark_data[3],
            "icr": benchmark_data[4],
            "currentRatio": benchmark_data[5],
            "dividentYield": benchmark_data[6],
            "percRandD": benchmark_data[7],
            "lastReturn": benchmark_data[8],
            "fiveYearAverageReturn": benchmark_data[9],
            "percentageMakingProfitLastFiveYears": benchmark_data[10]
        }
    else:
        benchmark_dict = {}  # Return an empty dictionary if no data is found
    
    # Step 4: Close the connection
    conn.close()
    
    return benchmark_dict

def verdict(parameter, value,profile):
    # Colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RESET = '\033[0m'
    
    # Extract the parameter profile details
    lower_bound, upper_bound, direction, exception = profile[parameter]
    # Determine the verdict based on the logic
    if direction == 'D':  # Downward logic
        if value < lower_bound:  # Below lower bound
            verdict = f"{GREEN}[+]"
        elif lower_bound <= value <= upper_bound:  # Within range
            verdict = f"{YELLOW}[~]"
        else:  # Above upper bound
            verdict = f"{RED}[-]"
        # Check the exception threshold if it exists
        if exception is not None and value < exception:
            verdict = f"{RED}[-]"

    elif direction == 'U':  # Upward logic
        if value < lower_bound:  # Below lower bound
            verdict = f"{RED}[-]"
        elif lower_bound <= value <= upper_bound:  # Within range
            verdict = f"{YELLOW}[~]"
        else:  # Above upper bound
            verdict = f"{GREEN}[+]"
        # Check the exception threshold if it exists
        if exception is not None and value > exception:
            verdict = f"{RED}[-]"

    # Reset color after verdict
    return verdict + RESET

def getEconomicData(db_path=dbLocation):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT date, inflation, ECBInterest, NL_Unemployment, NL_ConsumerConfidence, EUR_USD_ExchangeRate FROM economyhistory ORDER BY date DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    # If no data is found, return an empty dictionary
    if not result:
        return {}
    
    # Map the result to a dictionary
    keys = ["date", "inflation", "ECBInterest", "NL_Unemployment", "NL_ConsumerConfidence", "EUR_USD_ExchangeRate"]
    economy_data = dict(zip(keys, result))
    
    return economy_data

def print_formatted_output(data, benchmark, stockProfile, economicData):

    if not data:
        return

    try:
        formatted_date = datetime.strptime(data['date'], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        formatted_date = data['date']

    # Define rows for each section
    basic_info = [
        ["Ticker:", data['ticker'], "Inflation:", (str(economicData['inflation']) + " %")],
        ["Date:", formatted_date, "NL Unemploymentrate:", (str(economicData['NL_Unemployment']) + " %")],
        ["Name:", data['stockname'], "NL Consumer confidence:", (str(economicData['NL_ConsumerConfidence']) + " %")],
        ["Sector:", data['sector'], "ECB Interestrate:", (str(economicData['ECBInterest']) + " %")],
        ["Industry:", data['industry'], "EUR/Dollar exchange rate:", (str(round(economicData['EUR_USD_ExchangeRate'],2)) + " %")],
        ["Market:", data['Exchange']],
        ["Price:", format_currency(data['price'], scale=1, currency=data['currency'],decimals=2)]
    ]

    operations = [
        ["[*]", "Last Operating Income:", f"{format_currency(data['operatingIncome'], scale=1000000, currency=data['currency'], decimals=0)} million"],
        [verdict('percentageMakingProfitLastFiveYears', data['percentageMakingProfitLastFiveYears'], stockProfile), "Possitive operating incomelast 5 years:", format_percentage(data['percentageMakingProfitLastFiveYears']), format_benchmark(format_percentage(benchmark['percentageMakingProfitLastFiveYears']))],
        [verdict('percRandD',((data['rAndDExpense'] / data['revenue'])*100),stockProfile), "R&D expense as % of revenue:", format_percentage(((data['rAndDExpense'] / data['revenue'])*100)), format_benchmark(format_percentage(benchmark['percRandD']))],
        ["---", "-------------------------------------------------------","-----------------","-----------------"]
    ]

    debts = [
        [verdict('icr', data['icr'],stockProfile), "Interest Coverage Ratio:", data['icr'], format_benchmark(round(benchmark['icr'],2))],
        [verdict('currentRatio', data['currentRatio'], stockProfile), "Current Ratio:", data['currentRatio'], format_benchmark(round(benchmark['currentRatio'],2))],
        ["---", "-------------------------------------------------------","-----------------","-----------------"]
    ]

    fair_value = [
        [verdict('pbratio', data['pbRatio'], stockProfile), "P/B Ratio:", data['pbRatio'], format_benchmark(round(benchmark['pbratio'],2))],
        [verdict('peratio', data['peRatio'], stockProfile), "P/E Ratio:", data['peRatio'], format_benchmark(round(benchmark['peratio'],2))],
        [verdict('beta', data['beta'], stockProfile), "Beta:", data['beta'], format_benchmark(round(benchmark['beta'],2))],
        ["---", "-------------------------------------------------------","-----------------","-----------------"]
   ]

    earnings = [
        ["[*]", "Last Year Return:", format_percentage(data['lastReturn']), format_benchmark(format_percentage(benchmark['lastReturn']))],
        ["[*]", "5-Year Average Return:", format_percentage(data['fiveYearAvgReturn']), format_benchmark(format_percentage(benchmark['fiveYearAverageReturn']))],
        [verdict('dividentYield', data['dividendYield'], stockProfile), "Dividend Yield:", format_percentage(data['dividendYield']), format_benchmark(format_percentage(benchmark['dividentYield']))],
        ["---", "-------------------------------------------------------","-----------------","-----------------"]
    ]

    # Print sections
    print("\n")
    print("=" * 100)
    print("[ ****** Basic info ****** ]     [ ****** Latest economic parameters ****** ]")
    print("=" * 100)
    print(tabulate(basic_info, tablefmt="plain", colalign=("left", "left")))

    print("=" * 100)
    print("[ ****** Does the company generate cash out of its operations? ****** ]         \033[35m Industry Benchmark \033[0m")
    print("=" * 100)    
    print(tabulate(operations, tablefmt="plain", colalign=("left", "left")))
   
    print("=" * 100)
    print("[ ****** Can the company pay for its debts? ****** ]")
    print("=" * 100)
    print(tabulate(debts, tablefmt="plain", colalign=("left", "left")))

    print("=" * 100)
    print("[ ****** Is the value of the stock fair, given its risk? ****** ]")
    print("=" * 100)
    print(tabulate(fair_value, tablefmt="plain", colalign=("left", "left")))
  
    print("=" * 100)
    print("[ ****** What are my expected earnings? Note, based on historic data, so no guarantees at all ****** ]")
    print("=" * 100)
    print(tabulate(earnings, tablefmt="plain", colalign=("left", "left")))
    print("=" * 100)

def get_profile(profileID):
    # Profile formatted, lowerbound, upperbound, direction, red-flag | direction: (D=Down, meaning below upper bound is good, U=UP, meaning, above uppoer bound is good). 
    # red flag value indicates when a good value turns into bad again. often N/A, but for example, if dividendYield exceeds 10% the company is paying out irrationally, which should be investigated.
    
    profile = {}
    if(profileID == 1 ):
        profile = {
            "Type": 'Defensive profile',
            "beta": (0.99, 1.05, 'D', None),
            "peratio": (10, 20, 'D', None),
            "pbratio": (2, 5,'D', None),
            "icr": (5, 7,'U', None),
            "currentRatio": (0.95, 1.05,'U', None),
            "dividentYield": (3, 5,'U', 10),
            "percRandD": (1, 5, 'U', 25),
            "percentageMakingProfitLastFiveYears": (80, 99, 'U', None)
            }
    return profile

def generate_watchlist(profileID, easeFactor, dbLocation):
    # Get the profile based on the profileID
    profile = get_profile(profileID)

    # Open the database connection
    conn = sqlite3.connect(dbLocation)
    cursor = conn.cursor()

    # Retrieve relevant stock data
    query = """
        SELECT 
            s.id, s.ticker, s.stockname, s.Exchange, 
            sh.beta, sh.peratio, sh.pbratio, sh.icr, sh.currentRatio, 
            sh.dividentYield, sh.RandDExpense, sh.revenue, 
            sh.percentageMakingProfitLastFiveYears
        FROM Stocks s
        JOIN stockhistory sh ON s.id = sh.stockID
        WHERE sh.date = (
            SELECT MAX(date)
            FROM stockhistory sh2
            WHERE sh2.stockID = s.id
        )
    """
    cursor.execute(query)
    stocks = cursor.fetchall()

    # Columns fetched in query for readability
    columns = [
        "id", "ticker", "stockname", "Exchange",
        "beta", "peratio", "pbratio", "icr", "currentRatio",
        "dividentYield", "RandDExpense", "revenue",
        "percentageMakingProfitLastFiveYears"
    ]

    # Helper function to evaluate whether a value is within profile bounds
    def is_good(value, bounds):
        if value is None:
            return False
        lower, upper, direction, red_flag = bounds
        if direction == 'D':  # Downwards is good
            if red_flag is not None and value > red_flag:
                return False
            return value < lower * easeFactor
        elif direction == 'U':  # Upwards is good
            if red_flag is not None and value > red_flag:
                return False
            return value > upper / easeFactor

    # Process and filter stocks
    valid_stocks = []
    for stock in stocks:
        stock_data = dict(zip(columns, stock))

        try:
            # Calculate percRandD
            if stock_data["revenue"] and stock_data["RandDExpense"]:
                stock_data["percRandD"] = (stock_data["RandDExpense"] / stock_data["revenue"]) * 100
            else:
                stock_data["percRandD"] = None

            # Check for None values and validate criteria
            meets_criteria = all([
                stock_data.get("beta") is not None and is_good(stock_data["beta"], profile["beta"]),
                stock_data.get("peratio") is not None and is_good(stock_data["peratio"], profile["peratio"]),
                stock_data.get("pbratio") is not None and is_good(stock_data["pbratio"], profile["pbratio"]),
                stock_data.get("icr") is not None and is_good(stock_data["icr"], profile["icr"]),
                stock_data.get("currentRatio") is not None and is_good(stock_data["currentRatio"], profile["currentRatio"]),
                stock_data.get("dividentYield") is not None and is_good(stock_data["dividentYield"], profile["dividentYield"]),
                stock_data.get("percRandD") is not None and is_good(stock_data["percRandD"], profile["percRandD"]),
                stock_data.get("percentageMakingProfitLastFiveYears") is not None and is_good(stock_data["percentageMakingProfitLastFiveYears"], profile["percentageMakingProfitLastFiveYears"]),
            ])

            if meets_criteria:
                valid_stocks.append(stock_data)

        except Exception as e:
            # Skip stocks with errors (e.g., missing data, division by zero)
            print(f"Skipping stock {stock_data.get('ticker', 'Unknown')} due to error: {e}")

    conn.close()

    # Print the watchlist
    if valid_stocks:
        print("\nGenerated Watchlist:")
        print(tabulate(
            [[stock["id"], stock["ticker"], stock["stockname"], stock["Exchange"]] for stock in valid_stocks],
            headers=["ID", "Ticker", "Stock Name", "Exchange"],
            tablefmt="grid"
        ))
    else:
        print("\nNo stocks meet the criteria for this profile.")



# Actual program
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and display detailed stock information.",
        epilog="",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Add arguments
    parser.add_argument("ticker", type=str, nargs="?", help="Stock ticker symbol (e.g., ASML, PHG).")
    parser.add_argument("--listIndustries", action="store_true", help="List all industries.")
    parser.add_argument("--listStocksInIndustry", type=str, help="List stocks in a given industry by ID or name.")
    parser.add_argument("--generateWatchlist", action="store_true", help="Generate a watchlist based on selected profile.")
    parser.add_argument("--profileID", type=int, default=1, help="Profile ID to use for generating the watchlist. Default is 1 (Defensive profile).")
    parser.add_argument("--easeFactor",type=float,default=1.0,help="Ease factor to adjust parameter thresholds. Default is 1.0 (strict adherence to profile).")
    
    args = parser.parse_args()

    if args.listIndustries:
        list_industries()
    
    elif args.listStocksInIndustry:
        list_stocks_in_industry(args.listStocksInIndustry, dbLocation)
    
    elif args.generateWatchlist:
        # Generate a watchlist
        print("[*] Generating watchlist using Profile ID", args.profileID, "with Ease Factor",args.easeFactor,".")
        generate_watchlist(args.profileID, args.easeFactor, dbLocation)
    
    elif args.ticker:
        # If a ticker is provided, analyze the stock
        print("=" * 100)
        print("[ ****** Initializing analyzer ****** ]")
        print("=" * 100)
        
        # Fetch data from the database
        stock_data = get_stock_data(args.ticker)
        industry_id = stock_data["industryID"]
        benchmark_data = get_industry_benchmark_data(industry_id)
        screening_profile = get_profile(1)
        economicData = getEconomicData()
        print("[*] Screening stocks against the: ", screening_profile['Type'], ".")
        print("[*] Loading economic data from: ", economicData['date'], ".")
        
        # Print formatted output
        print_formatted_output(stock_data, benchmark_data, screening_profile, economicData)
    
    else:
        # No valid option provided
        parser.print_help()
