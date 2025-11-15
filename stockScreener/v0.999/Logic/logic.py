from flask import jsonify
from datetime import datetime
from flask import current_app
from collections import defaultdict
from Logic.database import *
import math
import random
from Static.content.quotes import quote_array


def get_random_quote():
    return random.choice(quote_array)
    
def logic_run_stock_screen(filters):

    # Base query with joins
    query = """
    SELECT Stocks.ticker, Stocks.stockname, Sectors.sector, stockhistory.peratio, stockhistory.price
    FROM Stocks
    JOIN Sectors ON Stocks.sectorID = Sectors.id
    JOIN stockhistory ON Stocks.id = stockhistory.stockID
    AND stockhistory.date = (
        SELECT MAX(date)
        FROM stockhistory AS sh
        WHERE sh.stockID = Stocks.id
    )
    WHERE 1=1
    """

    conditions = []
    values = []
    securityFilters = []

    # Sector filter
    if filters.get("sector") and filters["sector"] != "none":
        conditions.append("Stocks.sectorID = ?")
        values.append(filters["sector"])
        securityFilters.append(r"^\d+$")

    # Numeric range filters
    numeric_fields = {
        "pe_ratio": "stockhistory.peratio",
        "price": "stockhistory.price",
        "icr": "stockhistory.icr",
        "currentRatio": "stockhistory.currentRatio",
        "pbratio": "stockhistory.pbratio",
        "beta": "stockhistory.beta",
        "fiveYearAverageReturn": "stockhistory.fiveYearAverageReturn",
        "dividendYield": "stockhistory.dividentYield"
    }

    for key, column in numeric_fields.items():
        min_key = f"{key}_min"
        max_key = f"{key}_max"

        if filters.get(min_key):
            conditions.append(f"{column} >= ?")
            values.append(filters[min_key])
            securityFilters.append(r"^\d+(\.\d+)?$")

        if filters.get(max_key):
            conditions.append(f"{column} <= ?")
            values.append(filters[max_key])
            securityFilters.append(r"^\d+(\.\d+)?$")

    # Final query
    if conditions:
        query += " AND " + " AND ".join(conditions)

    results = two_dynamic_query_STRING_all(query, values, securityFilters)
    # Check if more than 50 results
    found = len(results)
    has_more = found > 50
    if has_more:
        results = results[:50]  # Trim to 50
    return results, found
    
def list_stocks():
    # Fetch stock tickers from portfolio transactions
    query = "SELECT DISTINCT Stocks.ticker, Stocks.id FROM portfolioTransactions JOIN Stocks ON portfolioTransactions.tickerid = Stocks.id;"  
    stocks = simple_query(query)
    return stocks
    
def logic_list_sectors():
    # Fetch all sectors from the Sectors table
    query = "SELECT id, sector FROM Sectors ORDER BY sector ASC;"
    sectors = simple_query(query)
    return sectors

def logic_list_industries():
    # Fetch all industries from the industries table
    query = "SELECT id, name FROM industries ORDER BY name ASC;"
    industries = simple_query(query)
    return industries


def list_industries():
    # Get overview of industries
    query = "SELECT i.id AS IndustryID, i.yahooname AS YahooName, COUNT(s.id) AS StockCount FROM industries i LEFT JOIN Stocks s ON i.id = s.industryID GROUP BY i.id, i.yahooname ORDER BY StockCount DESC;"
    data = simple_query(query)

    industries = []
    for row in data:
        industries.append({
            'industryID': row[0],
            'yahooname': row[1],
            'stockCount': row[2]
        })
    return industries

def list_personal_history():
    # Fetch expenses from expenses
    query = "SELECT * from personalFinance ORDER BY date DESC;"  
    financeHistory = simple_query(query)
    return financeHistory

def list_expenses():
    # Fetch expenses from expenses
    query = "SELECT * from expenses;"  
    expenses = simple_query(query)
    return expenses
    
def list_minimum_expenses():
    # Fetch expenses from expenses
    query = "SELECT * from expenses where survival = 1;"  
    expenses = simple_query(query)
    return expenses
    
def list_expense_types():
    # Fetch expense types
    query = "SELECT * from expenseType;"  
    expenseTypes = simple_query(query)
    return expenseTypes

def get_stock_by_industry(industry_id):
    query = "SELECT ticker, stockname, exchange FROM Stocks WHERE industryID = ?"
    data = simple_dynamic_query_INT(query,industry_id)

    stocks = []
    for row in data:
        stocks.append({
            'ticker': row[0],
            'stockname': row[1],
            'exchange': row[2]
        })
    return stocks

def get_latest_economic_data():
    query = "SELECT * FROM economyhistory ORDER BY date DESC LIMIT 1;"
    data = simple_query_one(query)
    
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
            'EU_CLI': data[11],
        }
    return {}
    
def smoothenEconomicData(economic_data):
    # Round EUR/USD exchange rate to two decimal places
    if 'EUR_USD_ExchangeRate' in economic_data:
        economic_data['EUR_USD_ExchangeRate'] = round(economic_data['EUR_USD_ExchangeRate'], 2)
        economic_data['EU_CLI'] = round(economic_data['EU_CLI'], 2)
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
        "Eu cli": {"icon": "fa-compass", "color": "indigo"},
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


#def get_all_profiles():
 #   query = "SELECT id, name FROM ProfileConfiguration"  # Adjust table/column names as per your schema
    #profiles = simple_query(query)
    #profiles = get_all_profiles()
    # Convert to a list of dictionaries for easier use in templates
    #return [{"id": profile[0], "name": profile[1]} for profile in profiles]
  #  return [{"id": 0, "name": "defensive"}]

def generate_watchlist(profile, easeFactor):
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
    stocks = simple_query(query)
    columns = [
        "id", "ticker", "stockname", "Exchange",
        "beta", "peratio", "pbratio", "icr", "currentRatio",
        "dividentYield", "RandDExpense", "revenue",
        "percentageMakingProfitLastFiveYears", "industry"
    ]
    valid_stocks = []

    def is_good(value, bounds):
        try:
            if value is None:
                return False
            lower, upper, direction, red_flag = bounds
            lower = float(lower)
            upper = float(upper)
            red_flag = float(red_flag) if red_flag else None
            
            if direction == 'D':
                if red_flag is not None and value > red_flag:
                    return False
                return value < lower * easeFactor
            elif direction == 'U':
                if red_flag is not None and value > red_flag:
                    return False
                return value > upper / easeFactor
        except Exception as e:
                    print(f"Error processing value {value} and bounds {bounds}: {e}")
    for stock in stocks:
        stock_data = dict(zip(columns, stock))
        try:
            if stock_data["revenue"] and stock_data["RandDExpense"]:
                stock_data["percRandD"] = (stock_data["RandDExpense"] / stock_data["revenue"]) * 100
            else:
                stock_data["percRandD"] = None
        except Exception as e:
            print(f"Error processing revenue or r&d expenses {stock}: {e}")
        
        try:
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
    return valid_stocks


    
def get_industry_benchmark_data(industry_id):
    query = "SELECT price, beta, peratio, pbratio, icr, currentRatio, dividentYield, percRandD, lastReturn, fiveYearAverageReturn, percentageMakingProfitLastFiveYears FROM industryBenchmark WHERE industryID = ?"
    benchmark_data = simple_dynamic_query_INT_one(query,industry_id)

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
    
    return benchmark_dict

def get_historic_stock_data(ticker):
    query = "SELECT MIN(date) AS firstBuyDate FROM portfolioTransactions WHERE tickerid = (SELECT id FROM Stocks WHERE ticker = ?) AND Type = 'Buy';"
    firstBuyDate = simple_dynamic_query_STRING_one(query, ticker, r'^[A-Za-z0-9]{1,5}$')[0]
    
    # Query returns the data closest to the buy date, preferably the buy date, applicatoin will enforce a data entry
    query = """
    SELECT s.id, s.ticker, s.stockname, s.Exchange, si.name, se.sector, sh.date, sh.price, sh.operatingIncom, sh.currentRatio,
        sh.icr, sh.pbratio, sh.peratio, sh.beta, sh.fiveYearAverageReturn, sh.lastReturn, sh.dividentYield, sh.revenue,
        sh.RandDExpense, sh.currency, sh.percentageMakingProfitLastFiveYears, si.id, s.isWatchlist, s.strategicEvaluation
    FROM Stocks s
    JOIN Sectors se ON s.sectorID = se.id
    JOIN industries si ON s.industryID = si.id
    JOIN stockhistory sh ON s.id = sh.stockID
    WHERE s.ticker = ? AND sh.date >= ?
    ORDER BY sh.date ASC
    LIMIT 1;
    """

    myInputs = [ticker,firstBuyDate]
    securityFilters = [r'^[A-Za-z0-9]{1,20}$', r'^\d{4}-\d{2}-\d{2}$']
    result = two_dynamic_query_STRING_one(query, myInputs,securityFilters)
    if not result:
        print(f"No data found for ticker: {ticker}")
        return None
        
    columns = [
        "id", "ticker", "stockname", "Exchange", "industry", "sector", "date", "price", "operatingIncome",
        "currentRatio", "icr", "pbRatio", "peRatio", "beta", "fiveYearAvgReturn",
        "lastReturn", "dividendYield", "revenue", "rAndDExpense", "currency", "percentageMakingProfitLastFiveYears","industryID", "isWatchlist", "strategicEvaluation"
    ]
    return enrich_stock_data(dict(zip(columns, result)))
    
def get_stock_data(ticker):
    query = """
    SELECT s.id, s.ticker, s.stockname, s.Exchange, si.name, se.sector, MAX(sh.date), sh.price, sh.operatingIncom, sh.currentRatio,
        sh.icr, sh.pbratio, sh.peratio, sh.beta, sh.fiveYearAverageReturn, sh.lastReturn, sh.dividentYield, sh.revenue,
        sh.RandDExpense, sh.currency, sh.percentageMakingProfitLastFiveYears, si.id, s.isWatchlist, s.strategicEvaluation
    FROM Stocks s
    JOIN Sectors se ON s.sectorID = se.id
    JOIN industries si on s.industryID = si.id
    JOIN stockhistory sh ON s.id = sh.stockID
    WHERE s.ticker = ?
    GROUP BY s.ticker
    ORDER BY MAX(sh.date) DESC
    LIMIT 1
    """
    # Assume that: a ticker symbol is not longer than 5 characters, has a normal alphabet and no special symbols: https://en.wikipedia.org/wiki/Ticker_symbol
    result = simple_dynamic_query_STRING_one(query, ticker, r'^[A-Za-z0-9]{1,5}$')
    if not result:
        print(f"No data found for ticker: {ticker}")
        return None
        
    columns = [
        "id", "ticker", "stockname", "Exchange", "industry", "sector", "date", "price", "operatingIncome",
        "currentRatio", "icr", "pbRatio", "peRatio", "beta", "fiveYearAvgReturn",
        "lastReturn", "dividendYield", "revenue", "rAndDExpense", "currency", "percentageMakingProfitLastFiveYears","industryID", "isWatchlist", "strategicEvaluation"
    ]
    return enrich_stock_data(dict(zip(columns, result)))

def stocksOwned(stockID):
    result = 0
    query = "SELECT  COALESCE(SUM(CASE WHEN Type = 'Buy' THEN quantity ELSE -quantity END), 0) AS stockOwned FROM portfolioTransactions WHERE tickerid = ?"
    result = simple_dynamic_query_INT(query, stockID)[0][0]
    return result



def get_watchlist():
    query = "SELECT s.id, s.ticker, s.stockname, i.yahooname FROM Stocks s JOIN industries i ON s.industryID = i.id WHERE s.isWatchlist = 1;"
    watchlist = simple_query(query)
    return watchlist
    
def get_dividend_top10():
    # Define the query to get the top 10 dividend yield stocks
    query = """
    WITH MostRecent AS (
        SELECT stockID, MAX(date) as recent_date
        FROM stockhistory
        GROUP BY stockID
    ),
    RecentDividends AS (
        SELECT sh.stockID, sh.dividentYield, sh.date
        FROM stockhistory sh
        JOIN MostRecent mr ON sh.stockID = mr.stockID AND sh.date = mr.recent_date
        WHERE (sh.dividentYield NOT LIKE 'inf') AND (sh.dividentYield < 20)
        ORDER BY sh.dividentYield DESC
        LIMIT 10
    )
    SELECT s.id, s.ticker, s.stockname, i.yahooname AS industry_name, rd.dividentYield, rd.date
    FROM Stocks s
    JOIN RecentDividends rd ON s.id = rd.stockID
    JOIN industries i ON s.industryID = i.id
    ORDER BY rd.dividentYield DESC
    LIMIT 10;
    """
    top_dividends = simple_query(query)
    return top_dividends

def get_pe_top10():
    # Define the query to get the top 10 dividend yield stocks
    query = """
    WITH MostRecent AS (
        SELECT stockID, MAX(date) as recent_date
        FROM stockhistory
        GROUP BY stockID
    ),
    RecentPE AS (
        SELECT sh.stockID, sh.peratio, sh.date
        FROM stockhistory sh
        JOIN MostRecent mr ON sh.stockID = mr.stockID AND sh.date = mr.recent_date
        WHERE (sh.peratio NOT LIKE 'inf') AND (sh.peratio > 0)
        ORDER BY sh.peratio ASC
        LIMIT 10
    )
    SELECT s.id, s.ticker, s.stockname, i.yahooname AS industry_name, rd.peratio, rd.date
    FROM Stocks s
    JOIN RecentPE rd ON s.id = rd.stockID
    JOIN industries i ON s.industryID = i.id
    ORDER BY rd.peratio ASC
    LIMIT 10;
    """
    bargains = simple_query(query)
    return bargains

def get_random_stocks():
    # Define the query to get 10 random stocks
    query = "SELECT s.id, s.ticker, s.stockname, i.yahooname AS industry_name FROM Stocks s JOIN industries i ON s.industryID = i.id ORDER BY RANDOM() LIMIT 10;"
    random_stocks = simple_query(query)    
    return random_stocks

def get_dividents():
    # Query to fetch dividend records along with stock tickers
    query = "SELECT Stocks.ticker, dividends.id, dividends.date, dividends.dividendPerShare FROM dividends JOIN Stocks ON dividends.stockID = Stocks.id"
    dividends = simple_query(query)
    # Return the results as a list of tuples
    return dividends
    
def get_all_transactions():
    query = "SELECT portfolioTransactions.id, portfolioTransactions.tickerid, Stocks.ticker, Stocks.stockname, portfolioTransactions.date, portfolioTransactions.quantity, portfolioTransactions.currency, portfolioTransactions.stockPrice, portfolioTransactions.Type, portfolioTransactions.transactionFee FROM portfolioTransactions JOIN Stocks ON portfolioTransactions.tickerid = Stocks.id;"
    transactions = simple_query(query)
    return transactions

def get_dividend_expectations():
    query = "SELECT Stocks.ticker, dividendExpectations.stockID, dividendExpectations.expectedMonth, dividendExpectations.expectedDividendPerShare, dividendExpectations.id, dividendExpectations.expectedDay FROM dividendExpectations JOIN Stocks ON dividendExpectations.stockID = Stocks.id"
    expectations = simple_query(query)
    return expectations

def calculate_dividend_expectations():
    query = """
    SELECT
        expectedMonth,
        Stocks.stockname,
        SUM(expectedDividendPerShare * portfolioTransactions.quantity) AS totalStockContribution
    FROM dividendExpectations
    JOIN portfolioTransactions ON dividendExpectations.stockID = portfolioTransactions.tickerid
    JOIN Stocks ON dividendExpectations.stockID = Stocks.id
    GROUP BY expectedMonth, Stocks.stockname
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
    END, Stocks.stockname;
    """

    sqlresult = simple_query_rowfactory(query)


    result = {
        "January": {"total": 0, "details": []},
        "February": {"total": 0, "details": []},
        "March": {"total": 0, "details": []},
        "April": {"total": 0, "details": []},
        "May": {"total": 0, "details": []},
        "June": {"total": 0, "details": []},
        "July": {"total": 0, "details": []},
        "August": {"total": 0, "details": []},
        "September": {"total": 0, "details": []},
        "October": {"total": 0, "details": []},
        "November": {"total": 0, "details": []},
        "December": {"total": 0, "details": []},
    }

   
  
    for row in sqlresult:
        month = row['expectedMonth']
        if month not in result:
            continue  # Skip unknown or malformed month values

        contribution = row['totalStockContribution']
        result[month]["total"] += contribution
        result[month]["details"].append({
            "stockname": row['stockname'],
            "contribution": contribution
        })

    return result


def calculate_dividends(stock_id):
    query = "SELECT id, date, quantity, stockPrice, Type, currency FROM portfolioTransactions WHERE tickerid = ? ORDER BY date"
    transactions = simple_dynamic_query_INT(query, stock_id)

    query2 = "SELECT date, dividendPerShare FROM dividends WHERE stockID = ? ORDER BY date"
    dividends = simple_dynamic_query_INT(query2, stock_id)
    
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

def get_latest_date():
    query = "SELECT MAX(date) FROM stockhistory"
    latest_date = simple_query_one(query)[0] 
    return latest_date

def get_fees():
    query = "SELECT SUM(transactionFee) FROM portfolioTransactions"
    result = simple_query_one(query)
    if result[0] is None:
        total_fee = 0
    else:
        total_fee = result[0]
    return total_fee

def getProfileConfigurations():
    query = "SELECT id, type FROM profiles"
    profiles = defaultdict(dict)
    
    profilesDB = simple_query(query)
    for profile_id, profile_type in profilesDB:
        profiles[profile_id]["Id"] = profile_id
        profiles[profile_id]["Type"] = profile_type
    
    query = "SELECT profile_id, metric, minValue, maxValue, direction, redFlag FROM profileMetrics"
    metrics = simple_query(query)
    for profile_id, metric, minValue, maxValue, direction, redFlag in metrics:
        profiles[profile_id][metric] = (minValue, maxValue, direction, redFlag)    
    return dict(profiles)
    
def get_portfolio_data():
   
    # Get latest exchange rate
    query = "SELECT EUR_USD_ExchangeRate FROM economyhistory ORDER BY date DESC LIMIT 1;"
    exchange_rate = simple_query_one(query)[0]
    
    # Fetch stock data only for stocks in portfolioTransactions
    query2 = "SELECT DISTINCT Stocks.id, Stocks.ticker, Stocks.stockname, Stocks.IndustryID, industries.yahooname FROM Stocks JOIN portfolioTransactions ON Stocks.id = portfolioTransactions.tickerid JOIN industries on Stocks.IndustryID = industries.ID"
    stocks = simple_query_rowfactory(query2)
    
    portfolio = []
    for stock in stocks:
        stock_id = stock['id']
        
        # Fetch invested and current value
        query3 = """
            SELECT
                Stocks.ticker,
                Stocks.stockname AS full_name,
                Stocks.assetType as assetType,
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
        """
        row = simple_dynamic_query_rowfactory_INT_one(query3, int(stock_id))
        
        # If we currently don't have the stock, don't display it. Note, it remains in the Database to calculate portfolio performance
        if(row['quantity'] != 0):
            
            invested = row['invested']
            current_value = row['latest_price'] * row['quantity']
            dividends = calculate_dividends(stock_id)
            
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
                "industry": stock['yahooname'],
                "currency": row['currency'],
                "assetType": row['assetType'],
                "return_percentage": return_percentage
            })
    return portfolio

def get_portfolio_statistics(pdata):
    pstatistics = []
    # return statistics
    total_invested = sum(stock['invested'] for stock in pdata)
    portfolio_value = sum(stock['current_value'] for stock in pdata)
    total_dividends = sum(stock['dividends'] for stock in pdata)
    total_fees = get_fees()
    total_return = ((portfolio_value - total_invested) / total_invested) * 100 if total_invested > 0 else 0
    
    # Diversification statistics
    # * Currency
    unique_currencies = set(stock['currency'] for stock in pdata)
    currencyExposure = []
    for currency in unique_currencies:
        curInvested = sum(stock['invested'] for stock in pdata if stock['currency'] == currency)
        exposure = round(curInvested / total_invested,3)
        
        currencyExposure.append({
            "currency": currency,
            "amount": round(curInvested,2),
            "exposure": exposure,
        })
    # * Asset Type
    unique_assets = set(stock['assetType'] for stock in pdata)
    assetExposure = []
    for asset in unique_assets:
        assInvested = sum(stock['invested'] for stock in pdata if stock['assetType'] == asset)
        exposure = round(assInvested / total_invested,3)
        assetExposure.append({
            "assetType": asset,
            "amount": round(assInvested,2),
            "exposure": exposure,
        })

    
    pstatistics.append({
        "total_invested": total_invested,
        "portfolio_value": portfolio_value,
        "total_fees": total_fees,
        "total_return": total_return,
        "currencyExposure": currencyExposure,
        "assetExposure": assetExposure,
        "total_dividends": total_dividends
    })
    return pstatistics

    
def portfolio_update_needed():
    today_date = datetime.today().strftime('%Y-%m-%d')
    query = "SELECT 1 FROM stockhistory WHERE date = ? LIMIT 1"
    securityFilter = r'^\d{4}-\d{2}-\d{2}$'
    result = simple_dynamic_query_STRING_one(query, today_date, securityFilter)
    if result is None:
        return True
    else:
        return False
        
def get_bonds():
    query = "select id, stockname from stocks where assetType = 'bond'"
    data = simple_query(query)
    return data

def get_etfs():
    query = "select id, stockname from stocks where assetType = 'etf'"
    data = simple_query(query)
    return data
    
def get_monthly_expenses():
    monthlyExpense = 0
    query = "select * from expenses where ((type != ?) and (type != ?))"
    myInputs = [Config.savings, Config.investments]
    securityFilters = [r'^\d+$', r'^\d+$']
    data = two_dynamic_query_STRING_all(query, myInputs,securityFilters)
    for item in data:
        if(item[3] == 12):
            monthlyExpense = monthlyExpense + (item[4]/1)
        if(item[3] == 4):
            monthlyExpense = monthlyExpense + (item[4]/4)
        if(item[3] == 6):
            monthlyExpense = monthlyExpense + (item[4]/6)
        if(item[3] == 1):
            monthlyExpense = monthlyExpense + (item[4]/12)         
    data = [(monthlyExpense)]
    return data

def get_monthly__minimal_expenses():
    monthlyExpense = 0
    query = "select * from expenses where ((survival = 1) and ((type != ?) and (type != ?)))"
    myInputs = [Config.savings, Config.investments]
    securityFilters = [r'^\d+$', r'^\d+$']
    data = two_dynamic_query_STRING_all(query, myInputs,securityFilters)
    for item in data:
        if(item[3] == 12):
            monthlyExpense = monthlyExpense + (item[4]/1)
        if(item[3] == 4):
            monthlyExpense = monthlyExpense + (item[4]/4)
        if(item[3] == 6):
            monthlyExpense = monthlyExpense + (item[4]/6)
        if(item[3] == 1):
            monthlyExpense = monthlyExpense + (item[4]/12)         
    data = [(monthlyExpense)]
    return data

def get_monthly_savings():
    query = "select sum(cost) from expenses where type = ?"
    data = simple_dynamic_query_INT(query, Config.savings)
    return data

def get_monthly_investments():
    query = "select sum(cost) from expenses where type = ?"
    data = simple_dynamic_query_INT(query, Config.investments)
    return data
    
def get_monthly_debt_payment():
    query = "select sum(cost) from expenses where type = ?"
    data = simple_dynamic_query_INT(query, Config.savings)
    return data

def get_recent_personal_situation():
    query = "select * from personalFinance ORDER BY date DESC LIMIT 1"
    data = simple_query(query)
    return data    

def get_monthly_debt():
    monthlyDebt = 0
    query = "select * from expenses where type = ?"

    data = simple_dynamic_query_INT(query, Config.debt)
    for item in data:
        if(item[3] == 12):
            monthlyDebt = monthlyDebt + (item[4]/1)
        if(item[3] == 4):
            monthlyDebt = monthlyDebt + (item[4]/4)
        if(item[3] == 6):
            monthlyDebt = monthlyDebt + (item[4]/6)
        if(item[3] == 1):
            monthlyDebt = monthlyDebt + (item[4]/12)         
    data = [(monthlyDebt)]
    return data  
 
def get_expenses_by_type():
    query = """
        SELECT
        et.expenseType,
        SUM(e.cost * e.frequency) AS totalAnnualCost,
        GROUP_CONCAT(e.expense || ' (€' || e.cost || ' x' || e.frequency || ')', ', ') AS expenseList
        FROM expenses e
        JOIN expenseType et ON e.type = et.id
        WHERE et.id NOT IN (?, ?)
        GROUP BY et.id
    """       
    
    myInputs = [Config.savings, Config.investments]
    securityFilters = [r'^\d+$', r'^\d+$']
    data = two_dynamic_query_STRING_all(query, myInputs,securityFilters)
    return data
    
# Fire stage:

# 0. Financial distress:	User relies on external source to supply cash, to make ends meet (e.g. parent/government/loan shark need to provide funding to pay bills)
# 1. Stable:		        User income is greater or equal than its (debts + expenses)
# 2. Fat stable:	        User income is greater or equal than its (debts + expenses), User has 3 months of (expenses + debts) in an emergency fund
# 2. Debt free:		        User is free of debt + ( income > expenses), has income to cover expenses, User has 3 months of (expenses + debt) in an emergency fund
# 3. Safety:		        User is free of debt, has income to cover expenses and has 3-5 years of expenses  
# 4. Security:		        User is free of debt, income from assets generate bare minimum of living expenses (taxes, utilities, food, shelter)
# 5. Barista Fire:	        User is free of debt, assets generate basic living expenses, small job is required to fullfill other live goals, luxery and hollidays
# 6. FIRE:			        Safe widraw rate of Assets generate monthly expenses + inflation correction, incuding allowance for fun


def calculateFireStage(monthlyExpenses, income, monthlyDebt, avg_monthly_dividends, savings, minimalExpenses):
    fireStage = "Dependent"
    if(income > monthlyExpenses):
        fireStage = "Stable situation"
        if((savings > 3* monthlyExpenses)):
            fireStage = "Stable with emergency fund"
            if(monthlyDebt == 0):
                fireStage = "Debt free with emergency fund"
                if(avg_monthly_dividends > minimalExpenses):
                    fireStage = "Barista FIRE"
                    if(avg_monthly_dividends > monthlyExpenses):
                        fireStage = "FIRE"
    return fireStage
# ************************** INSERT DATA ************************** #  

def addProfile(profileData):
    inputs = [profileData.get('profile_type')]
    query = "INSERT INTO profiles (type) VALUES (?);"
    securityFilters = [r'^[a-zA-Z0-9_]+$']
    insert_data(query, inputs, securityFilters)
    query = "SELECT id FROM profiles ORDER BY id DESC LIMIT 1;"
    newProfileID = simple_query_one(query)[0]
    metrics = ['beta', 'peRatio', 'pbRatio', 'icr', 'currentRatio', 'dividendYield', 'percRandD', 'percentageMakingProfitLastFiveYears']
    for metric in metrics:
        min_value = profileData.get(f'{metric}_min')
        max_value = profileData.get(f'{metric}_max')
        direction = profileData.get(f'{metric}_direction')
        redflag = profileData.get(f'{metric}_redflag')
        query = "INSERT INTO profileMetrics (profile_id, metric, minValue, maxValue, direction, redFlag) VALUES (?, ?, ?, ?, ?, ?)"
        inputs = [newProfileID, metric, min_value, max_value, direction, redflag]
        securityFilters = [r'^\d+$', r'^[a-zA-Z]+$', r'^\d+(\.\d+)?$', r'^\d+(\.\d+)?$', r'^[UD]$', r'^(\d+(\.\d+)?|NULL|null)?$',]
        insert_data(query, inputs, securityFilters)


def insert_dividend(myRequest):
    query = "INSERT INTO dividends (stockID, date, dividendPerShare) VALUES (?, ?, ?);"
    inputs = [int(myRequest.form.get('stock_id')), myRequest.form.get('record_date'), float(myRequest.form.get('dividend_per_share'))]
    securityFilters = [r'^\d+$', r'^\d{4}-\d{2}-\d{2}$', r'^\d+\.\d+$'] # Patterns for integer, month name, and float
    insert_data(query, inputs, securityFilters)

    
def insert_dividend_expectation(myRequest):
    query = "INSERT INTO dividendExpectations (stockID, expectedMonth, expectedDividendPerShare, expectedDay) VALUES (?, ?, ?, ?)"
    inputs = [int(myRequest.form['stock_id']), myRequest.form['month'], float(myRequest.form['expected_dividend']), float(myRequest.form['expectedDay'])] 
    securityFilters = [r'^\d+$', r'^[A-Za-z]{1,10}$', r'^\d+\.\d+$', r'^\d{4}-\d{2}-\d{2}$'] # Patterns for integer, month name, and float
    insert_data(query,inputs,securityFilters)
    
def insert_transaction(myRequest):
    ticker = myRequest.form['ticker']
    stock_id_query = "SELECT id FROM Stocks WHERE ticker = ?"
    # Assume that: a ticker symbol is not longer than 5 characters, has a normal alphabet and no special symbols: https://en.wikipedia.org/wiki/Ticker_symbol
    stock_id_result = simple_dynamic_query_STRING_one(stock_id_query, ticker, r'^[A-Za-z0-9]{1,20}$')

    if not stock_id_result:
        print("Couldn't find ticker: ", ticker)
    else:
        query = "INSERT INTO portfolioTransactions (tickerid, date, quantity, currency, stockPrice, Type, transactionFee) VALUES (?, ?, ?, ?, ?, ?, ?)"
        inputs = [int(stock_id_result[0]), myRequest.form['date'], float(myRequest.form['quantity']), myRequest.form['currency'], float(myRequest.form['stock_price']), myRequest.form['type'], float(myRequest.form['transaction_fee'])]
        securityFilters = [r'^\d+$', r'^\d{4}-\d{2}-\d{2}$', r'^\d+(\.\d{1,2})?$', r'^(EUR|USD)$', r'^\d+\.\d{1,2}$', r'^(Buy|Sell)$',r'^\d+\.\d{1,2}$']
        insert_data(query,inputs,securityFilters)
        
        # Try calculating expected dividends based on yahoo
 
def insert_expense_type(myRequest):
    query = "INSERT INTO expenseType (expenseType) VALUES (?);"
    inputs = [myRequest.form.get('expenseType')]
    securityFilters = [r'^[a-zA-Z0-9\s,+-]+$']
    insert_data(query, inputs, securityFilters) 
    
def insert_expense(myRequest):
    query = "INSERT INTO expenses (expense, type, frequency, cost, survival) VALUES (?, ?, ?, ?,?);"
    inputs = [myRequest.form.get('expense'), myRequest.form.get('type'), myRequest.form.get('frequency'), myRequest.form.get('cost'), myRequest.form.get('survival') ]
    securityFilters = [r'^[a-zA-Z0-9\s,+-]+$', r'^\d+$', r'^(0?[0-9]|1[0-2])$', r'^\d+(\.\d{1,2})?$',r'^[01]$']
    insert_data(query, inputs, securityFilters) 
    
def insert_personal_situation(myRequest):
    query = "INSERT INTO personalFinance (salary, date, savings) VALUES (?, ?, ?);"
    inputs = [myRequest.form.get('salary'), myRequest.form.get('date'), myRequest.form.get('savings')]
    securityFilters = [r'^\d+(\.\d{1,2})?$', r'^\d{4}-\d{2}-\d{2}$', r'^\d+(\.\d{1,2})?$']
    insert_data(query, inputs, securityFilters)
   



# ************************** DATA REMOVAL ************************** # 
def logic_delete_personal_situation(personal_situation_id):
    query = "DELETE FROM personalFinance WHERE id = ?"
    simple_dynamic_query_DELETE_INT(query, personal_situation_id)
   
def logic_delete_expense(expense_id):
    query = "DELETE FROM expenses WHERE id = ?"
    simple_dynamic_query_DELETE_INT(query, expense_id)

def delete_expense_type(category_id):
    query = "DELETE FROM expenseType WHERE id = ?"
    simple_dynamic_query_DELETE_INT(query, category_id)

def delete_dividend(dividend_id):
    query = "DELETE FROM dividends WHERE id = ?"
    simple_dynamic_query_DELETE_INT(query, dividend_id)


def delete_transaction(transaction_id):
    query = "DELETE FROM portfolioTransactions WHERE id = ?"
    simple_dynamic_query_DELETE_INT(query, transaction_id)

def delete_dividend_expectation(expectation_id):
    query = "DELETE FROM dividendExpectations WHERE id = ?"
    simple_dynamic_query_DELETE_INT(query,expectation_id)
    
def deleteProfile(profileID):
    if profileID == 1:
        return "Security violation"
    else:
        query = "DELETE FROM profileMetrics WHERE profile_id = ?"
        simple_dynamic_query_DELETE_INT(query, int(profileID))
        query = "DELETE FROM profiles WHERE id = ?"
        simple_dynamic_query_DELETE_INT(query, int(profileID))
        return "Profile deleted"
        
# ************************** UPDATE DATA ************************** #    

def logic_update_expense(expense_id, expense, e_type, frequency, cost, survival):
    print("Survival: ", survival)
    query = "UPDATE expenses SET expense = ?, type = ?, frequency = ?, cost = ?, survival=? WHERE id = ?;"
    inputs = [expense, e_type, frequency, cost, survival, expense_id]
    securityFilters = [r'^[a-zA-Z0-9\s,+-]+$', r'^\d+$', r'^(0?[0-9]|1[0-2])$', r'^\d+(\.\d{1,2})?$',r'^[01]$', r'^\d+$']
    update_data(query,inputs,securityFilters)

def logic_update_expense_category(category_id, category):
    query = "UPDATE expenseType SET expenseType = ? WHERE id = ?"
    inputs = [category, category_id]
    securityFilters = [r'^[a-zA-Z0-9\s,+-]+$', r'^\d+$']
    update_data(query,inputs,securityFilters)


def logic_update_watchlist(ticker, is_watchlist):
    query = "UPDATE Stocks SET isWatchlist = ? WHERE ticker = ?"
    inputs = [is_watchlist, ticker]
    securityFilters = [r'^[01]$',r'^[A-Za-z0-9]{1,5}$']
    update_data(query,inputs,securityFilters)

def logic_update_strategy(ticker, strategic_evaluation):
    query = 'UPDATE Stocks SET strategicEvaluation = ? WHERE ticker = ?'
    inputs = [strategic_evaluation, ticker]
    #\S is used for whitespace characters, allowing space, TAB, Enter Besides the alphabet (lower and capital) i'm also allowing these special cahracters: ,.$%+-= 
    # not allowing ' or ` to make it a bit harder + luckily the database query is parameterized :)
    securityFilters = [r'^[A-Za-z0-9\s\.,\$\*\(\)\%\+\-\=]*$', r'^[A-Za-z0-9]{1,5}$']
    update_data(query,inputs,securityFilters)
    
def updateProfile(data):
    profile_id = data.get('profile_id')
    metrics = ['beta', 'peRatio', 'pbRatio', 'icr', 'currentRatio', 'dividendYield', 'percRandD', 'percentageMakingProfitLastFiveYears']
    for metric in metrics:
        min_value = data.get(f'{metric}_min')
        max_value = data.get(f'{metric}_max')
        direction = data.get(f'{metric}_direction')
        redflag = data.get(f'{metric}_redflag')
        query = "UPDATE profileMetrics SET minValue = ?, maxValue = ?, direction = ?, redFlag = ? WHERE metric = ? AND profile_id = ?;"
        inputs = [min_value,max_value,direction,redflag, metric, profile_id]
        securityFilters = [r'^\d+(\.\d+)?$', r'^\d+(\.\d+)?$', r'^[UD]$', r'^(\d+(\.\d+)?|NULL|null)?$', r'^[a-zA-Z]+$', r'^\d+$']
        update_data(query,inputs,securityFilters)

def updateRecordedDividend(divID, recordDate, divPerShare):
    query="UPDATE dividends SET date=?, DividendPerShare=? where id = ?"
    inputs= [recordDate, divPerShare, divID]
    securityFilters = [r'^\d{4}-\d{2}-\d{2}$', r'^\d+(\.\d+)?$', r'^\d+$']
    update_data(query,inputs,securityFilters)


def updateExpectedDividend(divID, expectedMonth, divPerShare, expectedDay):
    query="UPDATE dividendExpectations SET expectedMonth=?, expectedDividendPerShare=?, expectedDay=? where id = ?"
    inputs= [expectedMonth, divPerShare, expectedDay, divID]
    securityFilters = [r'^[a-zA-Z]{3,12}$', r'^\d+(\.\d+)?$', r'^\d{4}-\d{2}-\d{2}$', r'^\d+$']
    update_data(query,inputs,securityFilters)
        
# ************************** Calculate stuff ************************** # 

def logic_years_to_target(FV, P, r):
    years = 1000                # if you can't calculate it (for example at first time use), lets set the default to 1000 years (aka unrealistic long)
    if P == 0 or r == 0:
        return years
    else:
        numerator = math.log((FV * r / P) + 1)
        denominator = math.log(1 + r)
        return numerator / denominator
    
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
    stock_data["ownedShares"] = stocksOwned(stock_data['id'])
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
    if value is None:
        smiley = SMILEY_RED.format(RED)
    else:       
        # Determine the verdict based on the logic
        if direction == 'D':  # Downward logic
            if value < lower_bound:  # Below lower bound
                smiley = SMILEY_GREEN.format(GREEN)
            elif lower_bound <= value <= upper_bound:  # Within range
                smiley = SMILEY_YELLOW.format(YELLOW)
            else:  # Above upper bound
                smiley = SMILEY_RED.format(RED)
            # Check the exception threshold if it exists
            if (exception is not None) and (exception != ""):
                exception = float(exception)
                if value < exception:
                    smiley = SMILEY_RED.format(RED)

        elif direction == 'U':  # Upward logic
            if value < lower_bound:  # Below lower bound
                smiley = SMILEY_RED.format(RED)
            elif lower_bound <= value <= upper_bound:  # Within range
                smiley = SMILEY_YELLOW.format(YELLOW)
            else:  # Above upper bound
                smiley = SMILEY_GREEN.format(GREEN)
            # Check the exception threshold if it exists
            if (exception is not None) and (exception != ""):
                exception = float(exception)
                if value > exception:
                    smiley = SMILEY_RED.format(RED)

    return smiley  # Return the smiley HTML