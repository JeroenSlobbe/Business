from flask import Flask, render_template, request, redirect, url_for

#from Config.profileConfiguration import *
import requests
from Config.config import *
from Logic.logic import *
from Logic.externalDataLogic import *
import uuid
import threading
import time
import jwt
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.config.from_object(Config)

    
@app.route("/")
def home():
    return render_template("home.html")  # Render a template for the home page

# Stock stuff
  
@app.route('/portfolio/view-portfolio', methods=['GET', 'POST'])
def view_portfolio():
    # Daily update own portfolio 
    if(bool(portfolio_update_needed())):
        try:
            APIAccessToken = get_jwt_token()
            headers = {'Authorization': f'Bearer {APIAccessToken}'}
            requestUrl = Config.dataURL + '/start-update-portfolio'
            response = requests.get(requestUrl, headers=headers)
        except requests.RequestException as e:
            print("Failed to update portfolio")

    if request.method == 'POST':
        # Handle deletion of a transaction
        transaction_id = request.form.get('transaction_id')
        if transaction_id:
            delete_transaction(transaction_id)
        return redirect(url_for('view_portfolio'))

    # Fetch data
    portfolio_data = get_portfolio_data()
    transactions = get_all_transactions()
    dividend_expectations = calculate_dividend_expectations()
    portfolio_statistics = get_portfolio_statistics(portfolio_data)
    
    # Calculations for dividend summary
    total_exp_dividends = 0    
    for row in dividend_expectations:
        total_exp_dividends = total_exp_dividends + dividend_expectations[row]
    
    avg_monthly_dividends = total_exp_dividends / 12
    annual_dividends = total_exp_dividends      

    return render_template('portfolio/portfolio_view.html', pstatistics=portfolio_statistics, portfolio=portfolio_data, avg_monthly_dividends=avg_monthly_dividends, annual_dividends=annual_dividends, dividend_expectations=dividend_expectations,transactions=transactions)
    

@app.route('/portfolio/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        # Handle deletion of a transaction
        transaction_id = request.form.get('transaction_id')
        if transaction_id:
            delete_transaction(transaction_id)
        return redirect(url_for('transactions'))

    # Fetch portfolio data and transactions
    portfolio_data = get_portfolio_data()
    transactions = get_all_transactions()

    return render_template('portfolio/transactions.html', portfolio=portfolio_data, transactions=transactions)


@app.route('/portfolio/fire', methods=['GET', 'POST'])
def fire_view():
    # Handle form submission for dividend record insertion or deletion
    if request.method == 'POST':
        if 'dividend_id' in request.form:  # Deleting a dividend
            dividend_id = request.form['dividend_id']
            delete_dividend(dividend_id)  # Call the delete function
        elif 'expectation_id' in request.form:  # Deleting a dividend expectation
            expectation_id = request.form['expectation_id']
            delete_dividend_expectation(expectation_id)  # Call the delete function
        else:  # Insert a new dividend
            insert_dividend(request)  # Call the insert function

        return redirect(url_for('fire_view'))

    # Fetch all recorded dividends and dividend expectations
    fire = get_dividents()  # Assuming this function returns dividend records
    expectations = get_dividend_expectations()  # Fetch dividend expectations
    stocks = list_stocks()  # Assuming this returns a list of stocks

    return render_template('portfolio/fire.html', fire=fire, stocks=stocks, expectations=expectations)


@app.route('/config/delete-profile', methods=['POST'])
def delete_profile():
    data = request.get_json()
    profile_id = data.get('profile_id')
    if profile_id == 1:
        return jsonify({'message': 'Profile ID 1 cannot be deleted'}), 400, {'Content-Type': 'application/json'}
    else:
        return jsonify({'message': deleteProfile(int(profile_id))}), 400, {'Content-Type': 'application/json'}
 
@app.route('/config/update-profile', methods=['POST'])
def update_profile(): 
    profile_id = request.form.get('profile_id')
    updateProfile(request.form)
    return jsonify({'message': 'profile updated'}), 400, {'Content-Type': 'application/json'}

        
    
# Market & stock selection stuff
@app.route('/stock-seeker/view-industries')
def view_industries():
    industries_data = list_industries()
    return render_template('stock-seeker/view_industries.html', industries=industries_data)

@app.route('/stock-seeker/search-profile')
def search_profile():
    profiles = getProfileConfigurations()  # Fetch all profiles
    watchlist = get_watchlist()
    dividendTopTen = get_dividend_top10()
    bargains = get_pe_top10()
    randomStocks = get_random_stocks()
    return render_template('stock-seeker/search_profile.html', profiles=profiles, watchlist=watchlist, dividendTopTen=dividendTopTen, bargains=bargains, randomStocks=randomStocks)


@app.route('/stock-seeker/evaluate-stock', defaults={'ticker': None, 'historicView': 0})
@app.route('/stock-seeker/evaluate-stock/<string:ticker>', defaults={'historicView': 0})
@app.route('/stock-seeker/evaluate-stock/<string:ticker>/<int:historicView>')
def evaluate_stock(ticker=None, historicView=0):
    # Get the latest economic data
    economic_data = smoothenEconomicData(get_latest_economic_data())
    profiles = getProfileConfigurations()
    profile = profiles[1]
    # If ticker is provided, fetch stock data
    if ticker:
        if historicView:
            stock_data = get_historic_stock_data(ticker)
            if stock_data:  # If stock data is available, get the industry benchmark
                industry_id = stock_data["industryID"]
                benchmark_data = get_industry_benchmark_data(industry_id)
                verdicts = generateVerdicts(stock_data, profile)
            else:
                verdicts = []
                benchmark_data = {}  # If stock data is not found, set benchmark data as empty
        else:
            stock_data = get_stock_data(ticker)  # Get the stock data using the ticker
            if stock_data:  # If stock data is available, get the industry benchmark
                industry_id = stock_data["industryID"]
                benchmark_data = get_industry_benchmark_data(industry_id)
                verdicts = generateVerdicts(stock_data, profile)
            else:
                verdicts = []
                benchmark_data = {}  # If stock data is not found, set benchmark data as empty
    else:
        stock_data = None
        benchmark_data = {}
        verdicts = {}
    return render_template('stock-seeker/evaluate_stock.html', historicView=historicView, ticker=ticker,economic_data=economic_data, stock_data=stock_data, benchmark_data=benchmark_data, profile=profile, verdicts=verdicts)  # Pass the benchmark data


# Manage data

@app.route('/update-data/refresh-economic-data', methods=['GET'])
def refresh_economic():
    return render_template('update-data/refresh_economic.html')

@app.route('/update-data/bonds', methods=['GET'])
def show_bonds():
    bonds = get_bonds()
    return render_template('update-data/bonds.html', exchanges=Config.exchanges, bonds=bonds)

@app.route('/update-data/etfs', methods=['GET'])
def etfs():
    etfs = get_etfs()
    return render_template('update-data/etfs.html', exchanges=Config.exchanges, etfs=etfs)

@app.route('/update-data/refresh-stock')
def refresh_stock():
    return render_template('update-data/refresh_stock.html')

@app.route('/update-data/refresh-industry-benchmark')
def refresh_industry_benchmark():
    return render_template('update-data/refresh_industry_benchmark.html')

@app.route('/update-data/import-tickers', methods=['GET'])
def refresh_tickers():
    return render_template('update-data/import_tickers.html')

# Manage data
@app.route('/config/profile', methods=['GET'])
def config_profile():
    profiles = getProfileConfigurations()
    return render_template('/config/profile_config.html', profiles=profiles)

# Everything AJAX 
@app.route('/industries', methods=['GET'])
def get_industries():
    industries = list_industries()  # Directly calling the function as it's now imported
    return jsonify(industries)

@app.route('/get_stocks_by_industry_route/<int:industry_id>')
def get_stocks_by_industry_route(industry_id):
    # Call the function to get stocks based on the industry ID
    stocks = get_stock_by_industry(industry_id)
    return jsonify(stocks)


@app.route('/stock-seeker/load-stocks/<int:profileID>/<easeFactor>', methods=['GET'])
def load_stocks(profileID, easeFactor):
    profiles = getProfileConfigurations()
    profile = profiles[1]  # Get the specific profile by ID
    easeFactor = float(easeFactor)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404  # Handle the case if profile is not found
    
    # Fetch the stocks from the database as done before
    stocks = generate_watchlist(profile, easeFactor)

    # Format the response
    stock_data = [{"ticker": stock["ticker"], "stockname": stock["stockname"], "industry": stock["industry"]} for stock in stocks]
    
    return jsonify({"stocks": stock_data})

# Inserting information in the database
@app.route('/portfolio/set-dividend-expectations', methods=['POST'])
def set_dividend_expectations():
    insert_dividend_expectation(request)
    return redirect(url_for('fire_view'))





## Fixing ajax
@app.route('/portfolio/update-dividend-expectation', methods=['POST'])
def update_dividend_expectation():
    divID = request.form['expectation_id']
    expectedMonth = request.form['expectedMonth']
    divPerShare = request.form['dps']    
    updateExpectedDividend(divID, expectedMonth, divPerShare)
    return redirect(url_for('fire_view') + "#expectedDividends")
    
@app.route('/portfolio/update-dividend-payout', methods=['POST'])
def update_dividend_payout():
    divID = request.form['dividend_id']
    recordDate = request.form['dividend_date']
    divPerShare = request.form['dps']
    updateRecordedDividend(divID,recordDate,divPerShare)
    return redirect(url_for('fire_view') + "#recordedDividends")


@app.route('/update_watchlist', methods=['POST'])
def update_watchlist():
    data = request.get_json()
    logic_update_watchlist(data['ticker'], data['isWatchlist'])
    return jsonify({'status': 'success'})

@app.route('/update_strategic_evaluation', methods=['POST'])
def update_strategic_evaluation():
    data = request.get_json()
    logic_update_strategy(data['ticker'], data['strategicEvaluation'])
    return jsonify({'status': 'success'})

# Variables available for all pages
@app.context_processor
def inject_latest_date(): 
    latest_date = get_latest_date()
    return {'latest_date': latest_date}
   
# Inserting information in the database comming from external source
@app.route('/portfolio/add-transaction', methods=['POST'])
def add_transaction():
    insert_transaction(request)
    # Prep request
    ticker = request.form['ticker']
    url = Config.dataURL + "/computeDividendExpectations/" + ticker
    headers = {'Authorization': f'Bearer {APIAccessToken}'}
    try:
        response = requests.get(url, headers=headers)
    except requests.RequestException as e:
        print("Error fetching dividends")
    return redirect('transactions')
   
# Deal with data comming from external sources, to seperate this (because at some point, I might let the OS trigger the fetching of data functions) its in a seperate data app

@app.route('/portfolio/add-bond', methods=['POST'])
def add_bond():
    bond = request.form['ticker']
    description = request.form['fullname']
    exchange = request.form['exchange']
    divYield = request.form['divYield']
    
    # Prepare the API request
    url = f"{Config.dataURL}/addBond/{bond}"
    headers = {'Authorization': f'Bearer {APIAccessToken}'}
    data = {
        'description': description,
        'exchange': exchange,
        'divYield':divYield
    }
    try:
        # Send POST request to the API
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for HTTP response codes >= 400
        print(response.json())  # Log the API response (optional)
    except requests.RequestException as e:
        print("Error fetching dividends:", e)

    return redirect('/update-data/bonds')

@app.route('/portfolio/add-etf', methods=['POST'])
def add_etf():
    etf = request.form['ticker']
    description = request.form['fullname']
    exchange = request.form['exchange']
    
    # Prepare the API request
    url = f"{Config.dataURL}/addETF/{etf}"
    headers = {'Authorization': f'Bearer {APIAccessToken}'}
    data = {
        'description': description,
        'exchange': exchange
    }
    try:
        # Send POST request to the API
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for HTTP response codes >= 400
        print(response.json())  # Log the API response (optional)
    except requests.RequestException as e:
        print("Error fetching dividends:", e)

    return redirect('/update-data/etfs')

@app.route('/start-update', methods=['GET', 'POST'])
def start_update():
    try:
        startURL = Config.dataURL + "/start-update"
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        response = requests.post(startURL, headers=headers)
        if response.status_code == 202:
            statusURL = Config.dataURL + "/status"
            return jsonify({}), 202, {'Location': statusURL}
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        print("Error: ", e)
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def task_status():
    #Fix for token refresh during long polling sessions
    global APIAccessToken
    try:
        decoded_token = jwt.decode(APIAccessToken, options={"verify_signature": False})
        expiry_time = decoded_token.get("exp")
        current_time = datetime.now(timezone.utc)
        five_minutes_before = (current_time - timedelta(minutes=5)).timestamp()
        if expiry_time <= five_minutes_before:
            APIAccessToken = get_jwt_token()
    except Exception as e:
        print(e)
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        statusURL = Config.dataURL + "/status"
        response = requests.get(statusURL, headers=headers)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/errors')
def get_errors():
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        errorURL = Config.dataURL + "/errors"
        response = requests.get(errorURL, headers=headers)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update-data/refresh-economic-data', methods=['POST'])
def refresh_economic_data():
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        economyURL = Config.dataURL + "/updateEconomics"
        response = requests.get(economyURL, headers=headers)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500        


@app.route('/update-data/refresh-benchmark-data', methods=['POST'])
def refresh_benchmark_data():
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        benchmarkURL = Config.dataURL + "/calculateBenchmarkData"
        response = requests.get(benchmarkURL, headers=headers)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500  

@app.route('/update-data/refresh-ticker-data', methods=['POST'])
def import_ticker_data():
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        refreshTickerURL = Config.dataURL + "/refresh-ticker-data"
        response = requests.post(refreshTickerURL, json={'exchange': request.json.get('exchange')}, headers=headers)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config/add-profile', methods=['POST'])
def add_profile():
    data = request.form
    addProfile(data)
    response = {'message': 'New profile added successfully'}
    return jsonify(response)

# Security related functions
def get_jwt_token():
    response = requests.post(Config.LOGIN_URL, json={'api_key': Config.DATA_APP_API_KEY})
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception('Failed to get JWT token')

@app.after_request
def apply_security_headers(response):
    nonce = uuid.uuid4().hex  # Generate a random nonce
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Feature-Policy'] = "geolocation 'self'; microphone 'none'; camera 'none'"
    response.headers['nonce'] = nonce  
    return response

def refresh_token_periodically():
    while True:
        global APIAccessToken
        APIAccessToken = get_jwt_token()
        time.sleep((int)(Config.JWT_ACCESS_TOKEN_EXPIRES - 10))  # Refresh 10 ms before the token expires
    
if __name__ == '__main__':
    APIAccessToken = get_jwt_token()
    token_refresh_thread = threading.Thread(target=refresh_token_periodically)
    token_refresh_thread.daemon = True
    token_refresh_thread.start()
    app.run(debug=Config.debug, port=Config.basePort)


