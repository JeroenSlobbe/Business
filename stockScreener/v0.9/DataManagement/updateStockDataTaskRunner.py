from flask import Flask, jsonify, url_for
import threading
import sqlite3
import yfinance as yf
from datetime import date, datetime, timedelta
import time
import random
import gc
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Shared data structure for tracking progress, errors, and task state
progress = {'time-started': '', 'total': 0, 'completed': 0, 'status': 'Pending'}
errors = []
task_running = False  # Flag to check if a task is already running

def update_database_task():
    global progress, errors, task_running
    task_running = True  # Set the flag to True when the task starts
    db_path = "../stockDB.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = date.today()
    
    # Build support structures
    cursor.execute("SELECT id, sector FROM Sectors")
    sector_dict = {row[1]: row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT id, yahooname FROM industries")
    industry_dict = {row[1]: row[0] for row in cursor.fetchall()}


    # Main logic
    startID = 0
    message = "Starting scraping, with collection date: " + str(timestamp) + " starting from record: " + str(startID)
    progress['time-started'] = str(timestamp)
    print(message)
    
    query = "SELECT id, ticker, stockname, exchange,industryID,sectorID FROM Stocks WHERE Status = 'active' and id > " + str(startID)
    cursor.execute(query)
    stocks = cursor.fetchall()
    total_stocks = len(stocks)
    progress['total'] = total_stocks
    
    # Main workload
    for i, (stock_id, ticker, name, exchange,industryID,sectorID) in enumerate(stocks):
        # Lets be gentle with yahoo and wait between half and one second after each record
        wait_time = random.uniform(0.5, 2.5)
        
        #Fix name so Yahoo can find them
        if(exchange == "XAMS"):
            ticker = ticker + ".AS"
        if(exchange == "XBRU"):
            ticker = ticker + ".BR"
        
        # Get stock data, note the web request is only made upon stock.info, stock.financials, etc.. so to limit the requests,. we will load stock.info into stock_info
        try:
            stock = yf.Ticker(ticker)
            stock_info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet        
            
        except Exception as e:           
            current_time = datetime.now()
            message = "[x] Sleeping for 2 minutes... starting at: " + str(current_time.strftime("%Y-%m-%d %H:%M:%S"))
            errors.append(message)
            print(message)
            time.sleep(120)
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
                message = "Fatal error while dealing with the rate limit: " + str(e)
                errors.append(message)
                print(message)
                continue
                #sys.exit()

        # Fix industry and sector data
        if (industryID is None):
            industry = stock_info.get("industry", "Unknown")
            if(industry != "Unknown"):
                indID = industry_dict.get(industry)
                cursor.execute("UPDATE Stocks SET industryID = ? WHERE id = ?", (indID, stock_id))
                conn.commit()

        if (sectorID is None):
            sector = stock_info.get("sector", "Unknown")
            if(sector != "Unknown"):
                secID = sector_dict.get(sector)
                cursor.execute("UPDATE Stocks SET sectorID = ? WHERE id = ?", (secID, stock_id))
                conn.commit()
                
        # Collect data we actually want
        price = stock_info.get("currentPrice", 0)
        book_value_per_share = stock_info.get("bookValue", 0)
        stockprice = stock_info.get("currentPrice", 0)
        eps = stock_info.get("trailingEps", 0)
        beta = stock_info.get("beta",0)
        currency_code = stock_info.get('currency')
        fiveyear_operating_income = 0
        operating_income = 0
        percentageMakingProfitLastFiveYears = 0
        
        try:
            fiveyear_operating_income = financials.loc['Operating Income'].tail(5)
            operating_income = fiveyear_operating_income[0]
        except Exception as e:
            # Probably a financial institution, trying income from continued operations
            try:
                 fiveyear_operating_income = financials.loc['Net Income From Continuing And Discontinued Operation'].tail(5)
                 operating_income = fiveyear_operating_income[0]
            except Exception as e:
                message = "Couldn't obtain operating income for: " + str(name) + "(" + str(ticker) + ")"
                errors.append(message)
                print("Couldn't obtain operating income for: ", name, "(",ticker,")")
        
        percentage_last_five_year_possitive_income = 0
        
        total_revenue = 0
        try:
            total_revenue = revenue = financials.loc["Total Revenue"][0]
        except Exception as e:
            message = "Couldn't obtain total revenue for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't obtain total revenue for: ", name, "(",ticker,")")
        ebit = 0
        try:
            ebit = financials.loc["EBIT", :][0]
        except Exception as e:
            message = "Couldn't obtain EBIT for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't obtain EBIT for: ", name, "(",ticker,")")
        
        interest_expense = 0
        try:
            interest_expense = financials.loc["Interest Expense", :][0]
        except Exception as e:
            message = "Couldn't obtain interest expense for: " + str(name) + "(" + str(ticker) + ")"
            errors.append(message)
            print("Couldn't obtain interest expense for: ", name, "(",ticker,")")
            
        
        current_assets = 0
        try:
            current_assets = balance_sheet.loc["Current Assets"][0]
        except Exception as e:
            pass
        
        current_liabilities = 0
        try:
            current_liabilities = balance_sheet.loc["Current Liabilities"][0]
        except Exception as e:
            pass
       
        dividend_yield = 0
        try:
            dividend_yield = round((stock_info.get('dividendYield')*100),2)
        except Exception as e:
            last_dividend = 0
            try:
                dividend_yield = stock_info.get('lastDividendValue') / stockprice
            except Exception as e:
                try:
                    historicData = stock.history(period="max")
                    average_dividends = historicData['Dividends'].mean()
                    dividend_yield = average_dividends / stockprice
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
                print("Due to absense of current liabilities or assets, couldn't compute the current ratio for: ", name, "(",ticker,")")
        
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
                r_d_expenses = stock.financials.loc["Research And Development"][0]
                rd_ratio = round(((r_d_expenses / total_revenue) * 100),2)    
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
        query = "INSERT INTO stockhistory (stockID,date,price,operatingIncom, percentageMakingProfitLastFiveYears, icr, currentRatio,pbratio, peratio,beta,lastReturn,fiveYearAverageReturn,dividentYield,RandDExpense,currency, revenue)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        cursor.execute(query, (stock_id, timestamp, price, operating_income,percentage_last_five_year_possitive_income, icr, current_ratio, pb_ratio, pe_ratio, beta, one_year_return, avg_return_over_5_years, dividend_yield, r_d_expenses, currency_code, total_revenue))
        conn.commit()

        progress['completed'] = i + 1
        progress['status'] = 'In Progress'
        
    progress['status'] = 'Completed'
    conn.close()
    task_running = False  # Reset the flag when the task is done

@app.route('/start-update', methods=['GET', 'POST'])
def start_update():
    global errors, task_running
    if task_running:
        return jsonify({'status': 'A task is already running'}), 403  # Return error if a task is already running
    
    errors.clear()  # Clear previous errors
    thread = threading.Thread(target=update_database_task)
    thread.start()
    return jsonify({}), 202, {'Location': url_for('task_status')}

@app.route('/status')
def task_status():
    global progress
    return jsonify(progress)

@app.route('/errors')
def get_errors():
    global errors
    return jsonify(errors)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
