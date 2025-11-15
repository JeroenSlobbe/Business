from flask import Flask, jsonify, url_for, request
import jwt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

import threading
import yfinance as yf
from datetime import date, datetime, timedelta
import time
import random
import math
import gc
import requests
from flask_cors import CORS
from Logic.database import *
from Logic.externalDataLogic import *
from Logic.dataComputations import *
from Config.config import *
from importlib.metadata import version

# Check if yfinance is up to date (other wise you get nasty errors)
packageName = "yfinance"
installed_version = version(packageName)
pypi_url = f"https://pypi.org/pypi/{packageName}/json"
latest_version = requests.get(pypi_url).json()["info"]["version"]

if installed_version != latest_version:
	print("[!] Please run: pip install --upgrade yfinance, as the libary is outdated")

# Note the majority of the functionality should be included in dataLogic.py, however as update_data_tasks is threat based (due to the long runtime)
# This wasn't possible, hence the exception.

app = Flask(__name__)
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES

#CORS(app)
jwt_manager = JWTManager(app)

# Shared data structure for tracking progress, errors, and task state
progress = {'time-started': '', 'total': 0, 'completed': 0, 'status': 'Pending'}
errors = []
task_running = False  # Flag to check if a task is already running

# return 0 instead of nan or inf 
def fixNaN(myInput):
    returnValue = myInput
    if isinstance(myInput, float) and math.isnan(myInput):
        returnValue = 0
    if isinstance(myInput, float) and math.isinf(myInput):
        returnValue = 0
    return returnValue
    
def handleException(e, messageText, ticker):
    print(e)
    message = messageText + " " + ticker
    errors.append(message)
    print(message)
    
def handleMessage(messageText, ticker):
    message = messageText + " " + ticker
    errors.append(message)
    print(message)

def evaluate_dividend_payout(myTicker, stock_id):            
        query = "SELECT assetType FROM Stocks WHERE id = ?"
        assetType = simple_dynamic_query_INT_one(query, stock_id)[0]
        
        # Note, need different function for a bond
        
        print(assetType)
        if assetType in ("bond"):
            query = "select expectedDividendPerShare, expectedDay from dividendExpectations where stockID=?"
            expectedBondPay = simple_dynamic_query_INT(query, stock_id)
            query = "select date from dividends where stockID=?"
            registeredBondPay = simple_dynamic_query_INT(query, stock_id)
            year = date.today().year
            today = date.today()
            
            # Note, assuming bond is only paid once a year on the same day
            dividendPerShare = expectedBondPay[0][0]

            registered_dates = {str(row[0]) for row in registeredBondPay}

            # Check each expected date
            for dividend, expected_day in expectedBondPay:
                # Replace year in expectedDay
                updated_date_str = year + expected_day[4:]
                # Check if already registered
                if updated_date_str in registered_dates:
                    print("bond allready up to date")
                else:
                    query_insert = "INSERT INTO dividends (stockID, date, dividendPerShare) VALUES (?, ?, ?)"
                    insertInputs = [stock_id, updated_date_str, dividend]
                    insertFilters = [r"^\d+$", r"^\d{4}-\d{2}-\d{2}$", r"^\d+(\.\d+)?$"]

                    insert_data(query_insert, insertInputs, insertFilters)
                    print(f"[+] Inserted new dividend for {myTicker} on {updated_date_str}.")

            
            
        if assetType in ("stock", "etf"):
            try:
                ticker = yf.Ticker(myTicker)
                #stock = yf.Ticker(ticker)
                dividend_history = ticker.history(period="1y", actions=True)
                dividends = ticker.dividends
                latest_dividend = dividends.iloc[-1] if not dividends.empty else "No dividends found"
                if not dividend_history.empty:
                        latest_paydate = dividend_history[dividend_history["Dividends"] > 0].index[-1].strftime("%Y-%m-%d")
                        # lets check if this is allready in the database:
                        query = "SELECT yahooDate FROM dividends WHERE stockID = ? AND yahooDate = ?"
                        myInputs = [stock_id, latest_paydate]
                        securityFilters = [r"^\d+$", r"^\d{4}-\d{2}-\d{2}$"]   
                        existing_entry = two_dynamic_query_STRING_one(query, myInputs, securityFilters)
                        
                        if not existing_entry:
                            # As Yahoo uses the declaration date, and I prefer the pay-date, lets also add the 'expectation' date
                            query = """
                                SELECT expectedDay
                                FROM dividendExpectations
                                WHERE stockID = ?
                                  AND substr(expectedDay, 6) > substr(?, 6)
                                ORDER BY substr(expectedDay, 6) ASC
                                LIMIT 1;
                            """
                            myInputs = [str(stock_id), latest_paydate]  # e.g. "2025-06-15"
                            securityFilters = [r"^\d+$", r"^\d{4}-\d{2}-\d{2}$"]
                            expectedDate = two_dynamic_query_STRING_one(query, myInputs, securityFilters)[0]
                            print("Expected date: ", expectedDate)
                            
                            query_insert = "INSERT INTO dividends (stockID, date, dividendPerShare, yahooDate) VALUES (?, ?, ?, ?)"
                            insertInputs = [stock_id, expectedDate, latest_dividend, latest_paydate]
                            insertFilters = [r"^\d+$", r"^\d{4}-\d{2}-\d{2}$", r"^\d+(\.\d+)?$", r"^\d{4}-\d{2}-\d{2}$"]

                            insert_data(query_insert, insertInputs, insertFilters)
                            print(f"[+] Inserted new dividend for {myTicker} on {latest_paydate}.")
               
                else:
                    message = "[!] no paydate found for: " + myTicker
                    errors.append(message)
                    print(message)
            
            except Exception as e:
                handleException(e, "[!] Couldn't update dividends for:", myTicker)
 
        elif assetType == "bond":
            print("Processing bond")
        else:
            print("Unknown asset type")
 
def fixExchange(exchange, ticker):
    #Fix name so Yahoo can find them
    if(exchange == "XAMS"):
        ticker = ticker + ".AS"
    if(exchange == "XBRU"):
        ticker = ticker + ".BR"
    return ticker
    

def fixIndustryID(industryID,stock_info, stock_id):
    query = "SELECT id, yahooname FROM industries"
    industry_dict = {row[1]: row[0] for row in simple_query(query)}
    if (industryID is None):
        industry = stock_info.get("industry", "Unknown")
        if(industry != "Unknown"):
            indID = industry_dict.get(industry)
            query = "UPDATE Stocks SET industryID = ? WHERE id = ?"
            inputs = [indID, stock_id]
            securityFilters = [r'^\d+$', r'^\d+$']
            update_data(query, inputs,securityFilters) 

def fixSectorID(sectorID, stock_info, stock_id):
    if (sectorID is None):
        sector = stock_info.get("sector", "Unknown")
        if(sector != "Unknown"):
            query = "SELECT id, sector FROM Sectors"
            sector_dict = {row[1]: row[0] for row in simple_query(query)}
            secID = sector_dict.get(sector)
            query = "UPDATE Stocks SET sectorID = ? WHERE id = ?"
            inputs = [secID, stock_id]
            securityFilters = [r'^\d+$', r'^\d+$']
            update_data(query, inputs,securityFilters)

def checkDelisted(stock_info, ticker, stock_id):
    delisted = False
    if not stock_info or "exchange" not in stock_info or "regularMarketPrice" not in stock_info:
        message = f"[!] Skipping {ticker}: possibly delisted or no market data available"
        errors.append(message)
        print(message)
        delisted = True
        query = "UPDATE Stocks SET status = 'delisted' WHERE id = ?"
        inputs = [stock_id]
        securityFilters = [r'^\d+$']
        update_data(query, inputs,securityFilters)
    return delisted


def update_database_task(scope):
    global progress, errors, task_running
    task_running = True  # Set the flag to True when the task starts
    timestamp = date.today()
    


    # Main logic
    startID = 0
    message = "Starting scraping, with collection date: " + str(timestamp) + " starting from record: " + str(startID)
    progress['time-started'] = str(timestamp)
    
    print("Starting with scope: ",scope)
    if (scope == "all"):        
        query = "SELECT id, ticker, stockname, exchange,industryID,sectorID, assetType FROM Stocks WHERE Status = 'active' and id > ?"
        stocks = simple_dynamic_query_INT(query, startID)
    else:
        query = "SELECT id, ticker, stockname, exchange,industryID,sectorID, assetType FROM Stocks WHERE Status = 'active' AND id IN (SELECT DISTINCT tickerid FROM portfolioTransactions);"
        stocks = simple_query(query)
    
    total_stocks = len(stocks)
    progress['total'] = total_stocks
    
    # Main workload
    for i, (stock_id, ticker, name, exchange,industryID,sectorID,assetType) in enumerate(stocks):
        # Lets be gentle with yahoo and wait between half and one second after each record
        wait_time = random.uniform(Config.randomSleepLow, Config.randomSleepHigh)
        
        ticker = fixExchange(exchange,ticker)

        
        # Check if dividends are being paid out
        if(scope == "portfolio"):
            evaluate_dividend_payout(ticker, stock_id)
    
        # Get stock data, note the web request is only made upon stock.info, stock.financials, etc.. so to limit the requests,. we will load stock.info into stock_info
        try:
            stock = yf.Ticker(ticker)
            stock_info = stock.info
            
            # Check if stock is delisted
            if(checkDelisted(stock_info, ticker, stock_id)):
                continue
   
            financials = stock.financials
            balance_sheet = stock.balance_sheet        
            
        except Exception as e:
            if "404 Client Error: Not Found for url" in str(e):
                handleException("", "[!] data not available for:", ticker)
            else:
                current_time = datetime.now()
                message = "[x] Sleeping for 2 minutes... starting at: " + str(current_time.strftime("%Y-%m-%d %H:%M:%S"))
                errors.append(message)
                print(message)
                time.sleep(Config.sleepTime)
                try:
                    # Lets be more aggressive in closing all sessions, deleting the object from memory, cleaning cache and and reload the lib
                    Session().close()
                    del stock
                    gc.collect()
                    importlib.reload(yf)
                    stock = yffo.Ticker(ticker)
                    if not stock:
                        message = "Failed to obtain data for: " + str(ticker) + ". Skipping this stock"
                        errors.append(message)
                        print(message)
                        continue
                    else:    
                        stock_info = stock.info
                        financials = stock.financials
                        balance_sheet = stock.balance_sheet  

                    current_time = datetime.now()
                    message = "[x] Continuing...: " + str(current_time.strftime("%Y-%m-%d %H:%M:%S"))
                    errors.append(message)
                    print(message)
                except Exception as e:
                    handleException(e, "Fatal error while dealing with the rate limit: " + str(e), ticker)
                    continue
                    #sys.exit()
        
        # Fix industry and sector data
        fixIndustryID(industryID, stock_info, stock_id)
        fixSectorID(sectorID, stock_info, stock_id)

                
        # Collect data we actually want
        if (assetType == "bond" or assetType == "etf"):
            try:
                price = stock_info.get("regularMarketPrice", 0)
            except Exception as e:
                message = "Couldn't obtain price for: " + str(name) + "(" + str(ticker) + ")"
                errors.append(message)
                print(message)
        else:
            try:
                price = stock_info.get("currentPrice", 0)
            except Exception as e:
                # This might be a government bond
                try:
                    price = stock_info.get("open", 0)
                except Exception as e:
                    message = "Couldn't obtain price for: " + str(name) + "(" + str(ticker) + ")"
                    errors.append(message)
                    print(message)   
        
        stockprice = price        
        
        try:
            book_value_per_share = stock_info.get("bookValue", 0)
            eps = stock_info.get("trailingEps", 0)
            beta = stock_info.get("beta",0)
        except Exception as e:
            message = "Couldn't obtain basic info for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print(message)         
        
        currency_code = stock_info.get('currency')
        # If we are not able to fetch the currency code, lets assume Brussel/Amsterdam are EUR and NYSE is Dollar
        if currency_code == None:
            if(exchange == "XAMS") or (exchange == "XBRU"):
                currency_code = "EUR"
            else:
                currency_code = "USD"
                
        fiveyear_operating_income = 0
        operating_income = 0
        percentageMakingProfitLastFiveYears = 0
        
        try:
            fiveyear_operating_income = financials.loc['Operating Income'].tail(5)
            operating_income = fiveyear_operating_income.iloc[0]
        except Exception as e:
            # Probably a financial institution, trying income from continued operations
            try:
                 fiveyear_operating_income = financials.loc['Net Income From Continuing And Discontinued Operation'].tail(5)
                 operating_income = fiveyear_operating_income.iloc[0]
            except Exception as e:
                message = "Couldn't obtain operating income for: " + str(name) + "(" + str(ticker) + ")"
                errors.append(message)
                print("Couldn't obtain operating income for: ", name, "(",ticker,")")
        
        percentage_last_five_year_possitive_income = 0
        
        total_revenue = 0
        try:
            total_revenue = revenue = financials.loc["Total Revenue"].iloc[0]
        except Exception as e:
            message = "Couldn't obtain total revenue for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't obtain total revenue for: ", name, "(",ticker,")")
        ebit = 0
        try:
            ebit = financials.loc["EBIT", :].iloc[0]
        except Exception as e:
            try:
                ni = financials.loc['Net Income From Continuing Operation Net Minority Interest'].iloc[0]
                ie = financials.loc['Interest Expense'].iloc[0]
                tp = stock.financials.loc['Tax Provision'].iloc[0]
                ebit = ni + ie + tp
            except Exception as e:    
                message = "Couldn't obtain EBIT for: " + str(name) + "(" + str(ticker) + ")"
                errors.append(message)
                print("Couldn't obtain EBIT for: ", name, "(",ticker,")")
        
        interest_expense = 0
        debt = 0
        try:
            debt = stock.balance_sheet.loc['Total Debt'].iloc[0]
        except Exception as e:
            message = "Couldn't obtain debt for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't obtain debt for: ", name, "(",ticker,")")            
        try:
            interest_expense = financials.loc["Interest Expense", :].iloc[0]
        except Exception as e:
            try:
                # If the company has no debt at all, its save to assume the interest expense is zero :)
                total_debt = stock.balance_sheet.loc['Total Debt'].iloc[0]
                if(total_debt == 0):
                    interest_expense = 0      
            except Exception as e:
                message = "Couldn't obtain interest expense for: " + str(name) + "(" + str(ticker) + ")"
                errors.append(message)
                print("Couldn't obtain interest expense for: ", name, "(",ticker,")")

        current_assets = 0
        try:
            current_assets = balance_sheet.loc["Current Assets"].iloc[0]
        except Exception as e:
            pass
        
        current_liabilities = 0
        try:
            current_liabilities = balance_sheet.loc["Current Liabilities"].iloc[0]
        except Exception as e:
            pass
       
        dividend_yield = 0
        if assetType == "bond":
            #Dividend yield of a bond should't change
            query = "SELECT dividentYield from stockhistory WHERE stockid = ? order by date DESC limit 1;"
            previousYield = simple_dynamic_query_INT_one(query, stock_id)
            dividend_yield = previousYield[0]
        else:
            # warrants/WARRANTS don't have dividends
            if "warrant" in str(name).lower():
                print("skipping: ", str(name), " as warrants don't have dividends")
            else:
                try:
                    dividend_yield = round((stock_info.get('dividendYield')),2)
                    if(dividend_yield < 0.001):
                        dividend_yield = 0
                except Exception as e:
                    last_dividend = 0
                    try:
                        dividend_yield = stock_info.get('lastDividendValue') / stockprice
                        if(dividend_yield < 0.001):
                            dividend_yield = 0
                    except Exception as e:
                        try:
                            historicData = stock.history(period="max")
                            average_dividends = historicData['Dividends'].mean()
                            dividend_yield = round((average_dividends / stockprice) * 100, 2) if stockprice else None
                            if(dividend_yield < 0.001):
                                dividend_yield = 0
                        except Exception as e:
                            message = "Couldn't obtain current divident yield for: " + str(name) + "(" + str(ticker) + ")"
                            errors.append(message)
                            print("Couldn't obtain current divident yield for: ", name, "(",ticker,")")

        pb_ratio = 0
        pe_ratio = 0
        r_d_expenses = 0
        icr = 0
        current_ratio = 0
        avg_return_over_5_years = 0
        one_year_return = 0
        
        
        # Make calculations
        try:
            pb_ratio = round((stockprice / book_value_per_share),2)
        except Exception as e:
            message = "Couldn't calculate pb ratio for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't calculate pb ratio for: ", name, "(",ticker,")")
            
        try:
            if(eps == 0):
                pe_ratio = 0
            else:
                pe_ratio = round((stockprice / eps),2)
        except Exception as e:
            message = "Couldn't calculate pe ratio for: " + str(name) + "(" + str(ticker) + ") due to: " + str(e)
            errors.append(message)
            print("Couldn't calculate pe ratio for: ", name, "(",ticker,") due to: ",e)            
        try:
            if(interest_expense == 0):
                icr = ebit
            else:
                icr = round((ebit / interest_expense),2)
        except Exception as e:
            message = "Couldn't calculate icr for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't calculate icr for: ", name, "(",ticker,")")            
            
        if((current_liabilities != 0) and (current_assets != 0)):
            current_ratio = round((current_assets / current_liabilities),2)
        else:
            try:
                current_ratio = stock_info.get('currentRatio')
            except Exception as e:
                message = "Due to absense of current liabilities or assets, couldn't compute the current ratio for: " + str(name) + "(" + str(ticker) + ")"
                errors.append(message)
                print(message)
        
        try:
            for year in fiveyear_operating_income:
                if year > 0:
                    percentage_last_five_year_possitive_income += 20
        except Exception as e:
            message = "Couldn't calculate avg alst years operating income for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't calculate avg alst years operating income for: ", name, "(",ticker,")")
            percentage_last_five_year_possitive_income = 0
        
        try:
            if "Research And Development" in stock.financials.index:
                r_d_expenses = stock.financials.loc["Research And Development"].iloc[0]
                #Peanalizing companies that don't publish their R&D as hard as companies that have a low one
                if(r_d_expenses == "nan"):
                    r_d_expenses = 0
                rd_ratio = round(((r_d_expenses / total_revenue) * 100), 2) if total_revenue else None 
        except Exception as e:
            message = "Couldn't obtain R&D expense: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't obtain R&D expense: ", name, "(",ticker,")")
            
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)
        five_years_ago = today - timedelta(days=(5*365))

        try:
            hist = stock.history(start=one_year_ago.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))
            hist5 = stock.history(start=five_years_ago.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))
            if len(hist) > 0:
                price_one_year_ago = hist['Close'].iloc[0]
                latest_price = hist['Close'].iloc[-1]
                one_year_return = round(((latest_price - price_one_year_ago) / price_one_year_ago) * 100,2)

            if len(hist5) > 0:
                price_five_years_ago = hist5['Close'].iloc[0]
                latest_price = hist5['Close'].iloc[-1]
                avg_return_over_5_years = round(((((latest_price - price_five_years_ago) / price_five_years_ago) * 100)/5),2)
        except Exception as e:
            message = "Couldn't calculate return statistics for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't calculate return statistics for: ", name, "(",ticker,")")

     
        # Store data in our database
        query = "INSERT INTO stockhistory (stockID,date,price,operatingIncom, percentageMakingProfitLastFiveYears, icr, currentRatio,pbratio, peratio,beta,lastReturn,fiveYearAverageReturn,dividentYield,RandDExpense,currency, revenue, debt)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?);"
        inputs = [stock_id, timestamp, fixNaN(price), fixNaN(operating_income),fixNaN(percentage_last_five_year_possitive_income), fixNaN(icr), fixNaN(current_ratio), fixNaN(pb_ratio), pe_ratio, fixNaN(beta), fixNaN(one_year_return), fixNaN(avg_return_over_5_years), fixNaN(dividend_yield), fixNaN(r_d_expenses), currency_code, fixNaN(total_revenue), fixNaN(debt)]
        securityFilters = [r'^\d+$', r'^\d{4}-\d{2}-\d{2}$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^(USD|GBP|EUR)?$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$']
        insert_data(query, inputs, securityFilters)

        progress['completed'] = i + 1
        progress['status'] = 'In Progress'
        
    progress['status'] = 'Completed'
    
    # Apply sector and industry bond fix

    task_running = False  # Reset the flag when the task is done
    fetch_and_store_benchmark_data()

@app.route('/start-update', methods=['GET', 'POST'])
@jwt_required()
def start_update():
    global errors, task_running
    if task_running:
        return jsonify({'status': 'A task is already running'}), 403  # Return error if a task is already running
    
    errors.clear()  # Clear previous errors
    scope = "all"
    thread = threading.Thread(target=update_database_task, args=(scope,))
    thread.start()
    return jsonify({}), 202, {'Location': url_for('task_status')}

@app.route('/start-update-portfolio', methods=['GET', 'POST'])   
@jwt_required() 
def update_portfolio():
    global errors, task_running
    if task_running:
        return jsonify({'status': 'A task is already running'}), 403  # Return error if a task is already running
    
    errors.clear()  # Clear previous errors
    scope = "portfolio"
    thread = threading.Thread(target=update_database_task, args=(scope,))
    thread.start()
    return jsonify({}), 202, {'Location': url_for('task_status')}

@app.route('/status')
@jwt_required()
def task_status():
    global progress
    return jsonify(progress)

@app.route('/errors')
@jwt_required()
def get_errors():
    global errors
    return jsonify(errors)
    
@app.route('/updateEconomics', methods=['GET', 'POST'])
@jwt_required()
def update_economics():
    fetch_and_store_economic_data()
    return jsonify({"message": "Economic data refreshed successfully!"})  

@app.route('/calculateBenchmarkData', methods=['GET', 'POST'])
@jwt_required()
def update_benchmark():
    fetch_and_store_benchmark_data()
    return jsonify({"message": "Benchmark recalculated!"})  
    
@app.route('/computeDividendExpectations/<ticker>', methods=['GET', 'POST'])
def computeDividendExpectations(ticker):
    dividends = computeExpectedDividends(ticker)
    return jsonify({"message": "Dividends calculated!"})  

@app.route('/addBond/<ticker>', methods=['GET', 'POST'])
@jwt_required()
def addBond(ticker):
    if request.method == 'POST':
        data = request.get_json()
        if data:
            description = data.get('description')
            exchange = data.get('exchange')
            divYield = data.get('divYield')
            dbticker = ticker
            
            query = "SELECT 1 FROM stocks WHERE ticker = ? LIMIT 1"
            securityFilter = r'^([A-Z]{2}[A-Za-z0-9]{9}\d|[A-Za-z0-9]{1,12})$'
            result = simple_dynamic_query_STRING_one(query, ticker, securityFilter)
            if result is None:         
                #Fix name so Yahoo can find them
                if(exchange == "XAMS"):
                    ticker = ticker + ".AS"
                if(exchange == "XBRU"):
                    ticker = ticker + ".BR"
                print(ticker, description,exchange)
                try:
                    stock = yf.Ticker(ticker)
                    stock_info = stock.info    
                    price = stock_info.get("regularMarketPrice", 0)
                    if (price != 0):
                        current_date = (datetime.now()).strftime("%Y-%m-%d")
                        status = 'special'
                        query = "INSERT INTO stocks (ticker, stockname, exchange, DateAdded, status, industryID, sectorID, assetType) VALUES (?, ?, ?, ?, ?, ?,?,?)"
                        inputs = [dbticker, description, exchange, current_date, status, Config.bondIndustryID, Config.bondSectorID, 'bond']
                        securityFilters = [r'^([A-Z]{2}[A-Za-z0-9]{9}\d|[A-Za-z0-9]{1,12})$', r'^[A-Za-z0-9\(\)\.\%\s]+$', r'^[A-Za-z]{1,6}$', r'^\d{4}-\d{2}-\d{2}$', r'^special$', r'^\d+$', r'^\d+$', r'^[A-Za-z]+$']
                        insert_data(query, inputs, securityFilters)
                        # Fetch ID
                        query = "SELECT id FROM stocks WHERE ticker = ?"
                        securityFilter = r'^([A-Z]{2}[A-Za-z0-9]{9}\d|[A-Za-z0-9]{1,12})$'
                        result = simple_dynamic_query_STRING_one(query, dbticker, securityFilter)
                        # Add price
                        query = "INSERT INTO stockhistory (stockID, date, price, dividentYield, currency) VALUES(?,?,?,?,?)"
                        inputs = [result[0], current_date, price, divYield,'EUR']
                        securityFilters = [r'^\d+$', r'^\d{4}-\d{2}-\d{2}$', r'^\d+(\.\d+)?$', r'^\d+(\.\d+)?$', r'^EUR$']
                        insert_data(query, inputs, securityFilters)
                    else:
                        return jsonify({"message": "Bond not added, ticker not available!"}) 
                    return jsonify({"message": "Bond added!"})  
                except Exception as e:
                    print(e)
                    return jsonify({"message": "Bond not added, ticker not available!"})  
            else:
                 return jsonify({"message": "Bond allready exists"})   


@app.route('/addETF/<ticker>', methods=['GET', 'POST'])
@jwt_required()
def addETF(ticker):
    if request.method == 'POST':
        data = request.get_json()
        if data:
            description = data.get('description')
            exchange = data.get('exchange')
            dbticker = ticker
            
            query = "SELECT 1 FROM stocks WHERE ticker = ? LIMIT 1"
            securityFilter = r'^([A-Z]{2}[A-Za-z0-9]{9}\d|[A-Za-z0-9]{1,12})$'
            result = simple_dynamic_query_STRING_one(query, ticker, securityFilter)
            if result is None:         
                #Fix name so Yahoo can find them
                if(exchange == "XAMS"):
                    ticker = ticker + ".AS"
                if(exchange == "XBRU"):
                    ticker = ticker + ".BR"
                if(exchange == "XETR"):
                    ticker = ticker + ".DE"                    

                try:
                    etf = yf.Ticker(ticker)
                    etf_info = etf.info    
                    print(etf_info)
                    price = etf_info.get("regularMarketPrice", 0)
                    if (price != 0):
                        current_date = (datetime.now()).strftime("%Y-%m-%d")
                        status = 'active'
                        query = "INSERT INTO stocks (ticker, stockname, exchange, DateAdded, status, industryID, sectorID, assetType) VALUES (?, ?, ?, ?, ?, ?,?,?)"
                        inputs = [dbticker, description, exchange, current_date, status, Config.etfIndustryID, Config.etfSectorID, 'etf']
                        securityFilters = [r'^([A-Z]{2}[A-Za-z0-9]{9}\d|[A-Za-z0-9]{1,12})$', r'^[A-Za-z0-9\-\(\)\.\%\s]+$', r'^[A-Za-z]{1,6}$', r'^\d{4}-\d{2}-\d{2}$', r'^active$', r'^\d+$', r'^\d+$', r'^[A-Za-z]+$']
                        insert_data(query, inputs, securityFilters)
                        # Fetch ID
                        query = "SELECT id FROM stocks WHERE ticker = ?"
                        securityFilter = r'^([A-Z]{2}[A-Za-z0-9]{9}\d|[A-Za-z0-9]{1,12})$'
                        result = simple_dynamic_query_STRING_one(query, dbticker, securityFilter)
                        # Add price
                        query = "INSERT INTO stockhistory (stockID, date, price, currency) VALUES(?,?,?,?)"
                        inputs = [result[0], current_date, price, 'EUR']
                        securityFilters = [r'^\d+$', r'^\d{4}-\d{2}-\d{2}$', r'^\d+(\.\d+)?$', r'^EUR$']
                        insert_data(query, inputs, securityFilters)
                    else:
                        return jsonify({"message": "ETF not added, ticker not available!"}) 
                    return jsonify({"message": "ETF added!"})  
                except Exception as e:
                    print(e)
                    return jsonify({"message": "ETF not added, ticker not available!"})  
            else:
                 return jsonify({"message": "ETF allready exists"})   


@app.route('/refresh-ticker-data', methods=['POST'])
@jwt_required()
def import_ticker_data():
    messages = import_and_update_tickers(request.json.get('exchange'))
    return jsonify({"status": "Update tickers successfully", "messages": messages})

# Access control
@app.route('/token', methods=['POST'])
def generate_token():
    if request.json.get('api_key') == Config.DATA_APP_API_KEY:
        current_time = datetime.now()
        access_token = create_access_token(identity='app.py')
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'msg': 'Invalid API key'}), 401

if __name__ == '__main__':
    app.run(debug=Config.debug, port=Config.dataPort)
